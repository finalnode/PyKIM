"""Kommandozeile für die lokale Lehrkraftseite des Abgabewegs."""

import argparse
import getpass
import json
from pathlib import Path

from .crypto import generate_course_credentials
from .teacher import create_teacher_report, decrypt_submission


def _password(value: str | None, *, confirm: bool = False) -> str:
    if value:
        return Path(value).expanduser().read_text(encoding="utf-8").strip()
    first = getpass.getpass("Passwort für den privaten Schlüssel: ")
    if confirm and first != getpass.getpass("Passwort wiederholen: "):
        raise ValueError("Die Passwörter stimmen nicht überein.")
    return first


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="PyKIM-Abgaben für Lehrkräfte")
    commands = result.add_subparsers(dest="command", required=True)
    keygen = commands.add_parser("keygen", help="Kurszertifikat und privaten Schlüssel erzeugen")
    keygen.add_argument("--teacher", required=True)
    keygen.add_argument("--school", required=True)
    keygen.add_argument("--course", required=True)
    keygen.add_argument("--output", type=Path, required=True)
    keygen.add_argument("--password-file", type=str)

    decrypt = commands.add_parser("decrypt", help="eine Abgabe entschlüsseln")
    decrypt.add_argument("submission", type=Path)
    decrypt.add_argument("--key", type=Path, required=True)
    decrypt.add_argument("--output", type=Path, required=True)
    decrypt.add_argument("--password-file", type=str)

    report = commands.add_parser("report", help="Bericht aus einem Moodle-Downloadordner erzeugen")
    report.add_argument("directory", type=Path)
    report.add_argument("--key", type=Path, required=True)
    report.add_argument("--output", type=Path, required=True)
    report.add_argument("--password-file", type=str)
    return result


def main(arguments: list[str] | None = None) -> None:
    options = parser().parse_args(arguments)
    if options.command == "keygen":
        certificate, private_key = generate_course_credentials(
            options.output,
            teacher=options.teacher,
            school=options.school,
            course=options.course,
            password=_password(options.password_file, confirm=True),
        )
        print(f"Öffentliches Schülerzertifikat: {certificate}")
        print(f"Privater Lehrerschlüssel: {private_key}")
        return
    password = _password(options.password_file)
    if options.command == "decrypt":
        payload = decrypt_submission(options.submission, options.key, password)
        options.output.parent.mkdir(parents=True, exist_ok=True)
        options.output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Entschlüsselt: {options.output}")
        return
    submissions = sorted(options.directory.rglob("*.pykim-abgabe"))
    if not submissions:
        raise SystemExit("Keine .pykim-abgabe-Dateien gefunden.")
    csv_path, html_path = create_teacher_report(
        submissions, options.key, password, options.output
    )
    print(f"CSV: {csv_path}")
    print(f"HTML: {html_path}")


if __name__ == "__main__":
    main()
