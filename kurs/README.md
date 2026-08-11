# PyKIM-Kursinhalte

Öffentliche Skripte, Aufgabenstellungen und deklarative Trainerdefinitionen
für die PyKIM Suite.

- `main` enthält den stabilen Unterrichtsstand.
- `beta` dient zur Erprobung neuer und geänderter Inhalte.
- Jede Aufgabe besitzt eine gleichnamige Datei unter `Trainer/`.
- `.pykim/hashes.json` wird durch GitHub Actions erzeugt und nicht von Hand gepflegt.

Nach Änderungen kann lokal geprüft werden:

```bash
python -m pip install "PyYAML>=6,<7"
python tools/validate_content.py --write-hashes
```

Schülerlösungen, Musterlösungen, Zertifikate, Schlüssel und personenbezogene
Daten gehören nicht in dieses Repository.
