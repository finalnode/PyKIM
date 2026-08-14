# Sicherheit

PyKIM ist eine Pythonbibliothek und keine Sicherheits-Sandbox. Programme, die
PyKIM importieren, sind regulärer Pythoncode und besitzen grundsätzlich die
Rechte des gestarteten Pythonprozesses.

Der deklarative Trainer lädt YAML-Definitionen und führt daraus keinen
beliebigen Pythoncode aus. Der Trainer kann jedoch den Zustand einer laufenden
PyKIM-Welt und den übergebenen Quelltext auswerten. Anwendungen müssen
Inhaltsordner validieren und Trainerstände nachvollziehbar versionieren.

Prozessisolation, Dateisystem- und Netzwerkberechtigungen, Zeit- und
Speichergrenzen sowie betriebssystemspezifische Sandboxmechanismen liegen in
der Verantwortung der aufrufenden Anwendung. Die Referenzanwendung
[in:si](https://github.com/finalnode/insi) dokumentiert ihr eigenes
Bedrohungsmodell separat.

Sicherheitslücken bitte zunächst vertraulich über den Repository-Inhaber
melden; Zugangsdaten, sensible Schülerdaten und funktionierende Exploits nicht
in einem öffentlichen Issue veröffentlichen.
