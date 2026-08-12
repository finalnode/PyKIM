# Änderungen

## 0.5.2

- Beispielgalerie um sichtbaren Laufstatus, Programmausgabe und Stop-Funktion ergänzt.
- Grafische Beispiele weisen während der Ausführung auf ihr separates Fenster hin.
- Kursimport zeigt Spinner, Fortschrittsbalken und einen verständlichen Arbeitshinweis.
- paralleler Download kleiner Kursdateien verkürzt den ersten Import deutlich.

## 0.5.1

- Kurslöschung reagiert ohne zusätzliches Zeichen auf den exakt eingegebenen Kursnamen.
- Desktop-Builds enthalten ein verlässliches CA-Bündel für den HTTPS-Abruf von Kursinhalten.
- Beispielkurs und Setupdatei sind direkt im Downloadbereich der README verlinkt.

## 0.5.0

- mehrere Kurse pro Installation samt kompakter Auswahl beim App-Start ergänzt
- `.pykim-setup`-Dateien direkt in der Kursauswahl importierbar gemacht
- Repository-Inhalte automatisch aus `Skripte/`, `Aufgaben/` und `Trainer/`
  entdeckt; Dateien und Ordner mit führendem `_` werden ignoriert
- getrennte, offline nutzbare Inhaltsstände pro Kurs eingerichtet
- automatischen Repo-Abgleich beim Kursstart und manuellen Refresh ergänzt
- freie Aufgaben ohne Trainer samt lokal gespeichertem Antwortfeld unterstützt
- Kursordner direkt aus der Auswahl im plattformspezifischen Dateimanager öffnen
- Kurse nach exakter Namensbestätigung sicher in den Systempapierkorb verschieben
- Versionsangabe des macOS-Bundles an `pyproject.toml` gekoppelt
- `get_position()` für imperative und objektorientierte Positionsabfragen ergänzt
- reproduzierbare PyInstaller-Builds für Windows und Linux ergänzt
- GitHub-Actions-Matrix für Windows, Linux, macOS Intel und Apple Silicon samt
  Release-Artefakten eingerichtet
- erfolgreiche Plattformpakete in getrennten `dist/releases`-Buildordnern
  gesammelt und bei Versionstags automatisch als GitHub Release veröffentlicht
- gemeinsamen Desktop-Einstieg und plattformgerechten eingebetteten
  Python-Runner eingeführt
- veralteten lokalen Kurs-Snapshot und betriebssystemgenerierte Dateien aus dem
  Repository entfernt

## 0.4.0

- `world.zoom()` als Kamera-Zoom umgesetzt: größere Weltpixel bei unveränderter
  Fenster- und Weltgröße
- Projektansicht zu einem Arbeitsbereich mit seitlicher Projektauswahl und
  breitem Python-Editor umgebaut
- `README.md` pro Schülerprojekt samt Markdown-Editor, Live-Vorschau und
  Reflexionsvorlage ergänzt
- atomare Speicherung und Konflikterkennung für Projektcode und Dokumentation
  eingebaut
- übernommene Pyxel-Beispiele sofort mit „Meine Projekte“ synchronisiert
- Python-Spielwiese um Syntaxhervorhebung sowie Ein- und Ausrücken mit
  `Tab`/`Shift+Tab` erweitert
- festen, kompakten Suite-Footer mit Repository-, Lizenz- und Herkunftshinweis
  ergänzt

## 0.3.0

- PyKIM Suite als lokale Desktop-Lernumgebung ausgebaut
- Kursinhalte von der App getrennt und per `.pykim-setup` konfigurierbar gemacht
- Skripte, Aufgaben und YAML-Trainer aus einem Kurs-Repository synchronisiert
- Trainerdateien vor Testläufen gegen ihre Repository-Hashes geprüft
- Aufgabenansicht, Testdetails, Codeeditor und Lernstand überarbeitet
- Thonny-, VS-Code- und Python-Laufzeiterkennung ergänzt
- Pyxel-Beispiele, Ressourceneditor und persönliche Projekte integriert
- Imperative und objektorientierte Lernwege getrennt strukturiert
- Mehrere Pixel, parallele Abläufe, Sichtbarkeit, Farben und Töne erweitert
- Persönliches Modul `erweiterungen.py` für eigene Funktionen und Klassen ergänzt
- macOS-App- und DMG-Build vorbereitet

## 0.2.0

- Erste zusammenhängende PyKIM-API, Traineraufgaben und NiceGUI-Prototypen
