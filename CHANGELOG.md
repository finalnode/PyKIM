# Änderungen

## Unveröffentlicht

## 0.6.0 – 2026-08-14

- die Desktop-Lernumgebung, Kursverwaltung, Autorenwerkstatt, Abgabe und
  Desktop-Builds in das eigenständige Repository
  [finalnode/insi](https://github.com/finalnode/insi) ausgelagert;
- den bisherigen Namespace `pykim.guide` sowie Suite-Abhängigkeiten aus dem
  PyKIM-Paket entfernt;
- PyKIM als unabhängig paketierbare Bibliothek auf Pyxel und fachliche
  Prüfbausteine reduziert;
- Kursregistry, interaktive Aktivitäten und Trainerfortschritt vollständig an
  eine optionale Host-Anwendung ausgelagert;
- `prepare(...)` und `run(check=...)` über einen neutralen
  `pykim.trainer_provider`-Entry-Point angebunden, ohne in:si zu importieren;
- reproduzierbaren, in CI geprüften Wheel-Bau aus einer frischen Quellkopie
  ergänzt, damit lokale Build-Altstände nicht in PyKIM-Pakete gelangen;
- veränderlichen Zustand für Position, Welt, Audio und Animation in einer
  gebundenen `Runtime`-Standardinstanz zusammengeführt;
- farbbasierte Hindernisse, Hintergrundfarben, Nachbarschaftserkennung und
  Sammelobjekte ergänzt.

## 0.5.5

Letzter gemeinsamer Release von PyKIM und der damaligen PyKIM Suite. Die
vollständige historische Suite-Chronik wird im
[in:si-Repository](https://github.com/finalnode/insi/blob/main/CHANGELOG.md)
fortgeführt; ältere Änderungen bleiben außerdem in der Git-Historie erhalten.
