"""Kurszertifikate und hybride Verschlüsselung für Offline-Abgaben."""

import base64
import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidSignature
from cryptography.x509.oid import NameOID

CERTIFICATE_FORMAT = "pykim-course-certificate-v1"
PRIVATE_KEY_FORMAT = "pykim-teacher-private-key-v1"
SUBMISSION_FORMAT = "pykim-submission-v1"


@dataclass(frozen=True)
class CertificateInfo:
    teacher: str
    school: str
    course: str
    valid_from: str
    valid_until: str
    fingerprint: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def _json_bytes(data: dict[str, object]) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"), validate=True)


def _slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return result or "pykim-kurs"


def certificate_info(data: bytes | str | Path) -> CertificateInfo:
    """Prüfe das öffentliche Zertifikat und liefere seine Kursangaben."""
    raw = Path(data).read_bytes() if isinstance(data, Path) else (
        data.encode("utf-8") if isinstance(data, str) else data
    )
    document = json.loads(raw.decode("utf-8"))
    if document.get("format") != CERTIFICATE_FORMAT:
        raise ValueError("Die Datei ist kein unterstütztes PyKIM-Kurszertifikat.")
    certificate = x509.load_pem_x509_certificate(document["certificate_pem"].encode("ascii"))
    try:
        certificate.public_key().verify(
            certificate.signature,
            certificate.tbs_certificate_bytes,
            padding.PKCS1v15(),
            certificate.signature_hash_algorithm,
        )
    except InvalidSignature as error:
        raise ValueError("Die Signatur des Kurszertifikats ist ungültig.") from error
    fingerprint = certificate.fingerprint(hashes.SHA256()).hex()
    if fingerprint != document.get("fingerprint"):
        raise ValueError("Der Zertifikatsfingerabdruck stimmt nicht.")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if now < certificate.not_valid_before or now > certificate.not_valid_after:
        raise ValueError("Das Kurszertifikat ist noch nicht oder nicht mehr gültig.")
    metadata = document.get("metadata", {})
    def subject_value(oid: x509.ObjectIdentifier) -> str:
        values = certificate.subject.get_attributes_for_oid(oid)
        return values[0].value if values else ""

    signed_metadata = {
        "teacher": subject_value(NameOID.COMMON_NAME),
        "school": subject_value(NameOID.ORGANIZATION_NAME),
        "course": subject_value(NameOID.ORGANIZATIONAL_UNIT_NAME),
    }
    if any(str(metadata.get(key, "")) != value for key, value in signed_metadata.items()):
        raise ValueError("Die Kursangaben passen nicht zum signierten Zertifikat.")
    return CertificateInfo(
        teacher=signed_metadata["teacher"],
        school=signed_metadata["school"],
        course=signed_metadata["course"],
        valid_from=certificate.not_valid_before.isoformat(),
        valid_until=certificate.not_valid_after.isoformat(),
        fingerprint=fingerprint,
    )


def generate_course_credentials(
    output_directory: str | Path,
    *,
    teacher: str,
    school: str,
    course: str,
    password: str,
    valid_days: int = 730,
) -> tuple[Path, Path]:
    """Erzeuge öffentliches Schülerzertifikat und verschlüsselten Lehrerschlüssel."""
    if len(password) < 8:
        raise ValueError("Das Passwort für den privaten Schlüssel benötigt mindestens 8 Zeichen.")
    if not all(value.strip() for value in (teacher, school, course)):
        raise ValueError("Lehrkraft, Schule und Kurs müssen angegeben werden.")
    root = Path(output_directory).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    now = datetime.now(timezone.utc)
    subject = x509.Name([
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, school.strip()),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, course.strip()),
        x509.NameAttribute(NameOID.COMMON_NAME, teacher.strip()),
    ])
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=valid_days))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )
    fingerprint = certificate.fingerprint(hashes.SHA256()).hex()
    certificate_document = {
        "format": CERTIFICATE_FORMAT,
        "metadata": {"teacher": teacher.strip(), "school": school.strip(), "course": course.strip()},
        "fingerprint": fingerprint,
        "certificate_pem": certificate.public_bytes(serialization.Encoding.PEM).decode("ascii"),
    }
    private_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.BestAvailableEncryption(password.encode("utf-8")),
    )
    private_document = {
        "format": PRIVATE_KEY_FORMAT,
        "fingerprint": fingerprint,
        "course": course.strip(),
        "encrypted_private_key_pem": private_pem.decode("ascii"),
    }
    stem = _slug(course)
    certificate_path = root / f"{stem}.pykim-cert"
    private_path = root / f"{stem}.pykim-private-key"
    certificate_path.write_text(json.dumps(certificate_document, ensure_ascii=False, indent=2), encoding="utf-8")
    private_path.write_text(json.dumps(private_document, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.chmod(private_path, 0o600)
    except OSError:
        pass
    return certificate_path, private_path


def encrypt_payload(payload: dict[str, object], certificate_data: bytes) -> dict[str, object]:
    document = json.loads(certificate_data.decode("utf-8"))
    info = certificate_info(certificate_data)
    certificate = x509.load_pem_x509_certificate(document["certificate_pem"].encode("ascii"))
    header = {
        "format": SUBMISSION_FORMAT,
        "encryption": "RSA-OAEP-SHA256+AES-256-GCM",
        "key_id": info.fingerprint,
        "course": info.course,
    }
    content_key = AESGCM.generate_key(bit_length=256)
    nonce = os.urandom(12)
    ciphertext = AESGCM(content_key).encrypt(nonce, _json_bytes(payload), _json_bytes(header))
    encrypted_key = certificate.public_key().encrypt(
        content_key,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )
    return {**header, "encrypted_key": _b64(encrypted_key), "nonce": _b64(nonce), "ciphertext": _b64(ciphertext)}


def decrypt_payload(
    envelope: dict[str, object], private_key_data: bytes, password: str
) -> dict[str, object]:
    private_document = json.loads(private_key_data.decode("utf-8"))
    if private_document.get("format") != PRIVATE_KEY_FORMAT:
        raise ValueError("Die Datei ist kein unterstützter PyKIM-Lehrerschlüssel.")
    if envelope.get("format") != SUBMISSION_FORMAT:
        raise ValueError("Die Datei ist keine unterstützte PyKIM-Abgabe.")
    if envelope.get("key_id") != private_document.get("fingerprint"):
        raise ValueError("Abgabe und privater Schlüssel gehören nicht zusammen.")
    key = serialization.load_pem_private_key(
        private_document["encrypted_private_key_pem"].encode("ascii"),
        password=password.encode("utf-8"),
    )
    content_key = key.decrypt(
        _unb64(str(envelope["encrypted_key"])),
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )
    header = {name: envelope[name] for name in ("format", "encryption", "key_id", "course")}
    plaintext = AESGCM(content_key).decrypt(
        _unb64(str(envelope["nonce"])),
        _unb64(str(envelope["ciphertext"])),
        _json_bytes(header),
    )
    result = json.loads(plaintext.decode("utf-8"))
    if not isinstance(result, dict):
        raise ValueError("Der entschlüsselte Inhalt ist ungültig.")
    return result
