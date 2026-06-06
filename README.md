# 🌿🤖 Handwise-HA

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-41BDF5.svg)](https://www.home-assistant.io/)
[![GitHub release](https://img.shields.io/github/v/release/MTTPoll/handwise-ha?display_name=tag)](https://github.com/MTTPoll/handwise-ha/releases)
[![GitHub issues](https://img.shields.io/github/issues/MTTPoll/handwise-ha)](https://github.com/MTTPoll/handwise-ha/issues)
[![License](https://img.shields.io/github/license/MTTPoll/handwise-ha)](LICENSE)

**Handwise-HA** is a Home Assistant custom integration for **Handwise robotic lawn mowers**.

It connects your mower to Home Assistant and provides status information, mower controls, diagnostics, battery data, mowing progress, rain detection and more through the Handwise / Anthbot cloud platform.

> Currently tested with the **Handwise MGC01 500**.  
> Other Handwise mower models using the same cloud platform may also work.

---

## Language

- [English](#english)
- [Deutsch](#deutsch)

---

# English

## ✨ Features

Handwise-HA currently supports:

- 🌿 Native Home Assistant lawn mower entity
- ▶️ Start mowing
- ⏸️ Pause mowing
- 🏠 Return to charging station
- 🔋 Battery level
- 📡 Connection status
- 🔌 Charging status
- 📊 Mowing progress
- 📐 Mowed area
- ✂️ Cutting height
- 📶 Wi-Fi signal strength
- ⚠️ Error code reporting
- 🌧️ Rain detection
- 🔐 PIN / lock status
- 🧪 Diagnostic sensors
- 🗺️ Current path diagnostic data

---

## ✅ Supported Models

### Confirmed working

| Brand | Model | Status |
|---|---|---|
| Handwise | MGC01 500 | ✅ Tested |

### Potentially compatible

This integration may also work with other Handwise robotic lawn mowers using the same Handwise / Anthbot cloud platform.

Possible candidates:

- Other Handwise robotic mower models
- Anthbot Genie based mower models
- Future Handwise cloud-connected mower models

If your mower works with the **Handwise** or **Anthbot** mobile app, there is a chance that it can work with this integration.

Please open an issue if you successfully test another model.

---

## 📦 Installation

### HACS installation

1. Open **HACS**
2. Go to **Integrations**
3. Open the menu in the top right corner
4. Select **Custom repositories**
5. Add this repository URL:

```text
https://github.com/MTTPoll/handwise-ha
```

6. Select category:

```text
Integration
```

7. Install **Handwise-HA**
8. Restart Home Assistant

---

### Manual installation

Copy this folder:

```text
custom_components/handwise_ha
```

to your Home Assistant configuration directory:

```text
config/custom_components/handwise_ha
```

Then restart Home Assistant.

---

## ⚙️ Configuration

After installation:

1. Open Home Assistant
2. Go to:

```text
Settings → Devices & services → Add integration
```

3. Search for:

```text
Handwise-HA
```

4. Enter your Handwise account credentials
5. Select your mower
6. Complete setup

---

## 🧩 Available Entities

The exact entities can differ depending on the mower model and firmware.

### Lawn mower

- Lawn mower control entity
- Start mowing
- Pause mowing
- Return to charging station

### Sensors

- Battery level
- Mower status
- Mowing progress
- Mowed area
- Cutting height
- Wi-Fi signal
- Error code
- Event code
- IP address
- PIN status
- Rain effect
- Rain wait time
- Firmware information
- Current path diagnostic data

### Binary sensors

- Connection
- Charging
- Rain detection
- Error state
- Safety trigger

### Controls

- Cutting height
- Rain detection
- Rain wait time

---

## 🧪 Diagnostics

Handwise-HA includes diagnostic entities that can help with troubleshooting and future development.

Examples:

- Error code
- Event code
- Wi-Fi signal
- Firmware versions
- Current path data
- Internal mower status

The current path data is currently exposed for diagnostics only. Map or route visualization may be added later.

---

## 🏡 Dashboard ideas

Handwise-HA works with normal Home Assistant dashboard cards.

Recommended cards:

- Tile Card
- Entities Card
- Mushroom Cards
- Custom dashboard cards

Example dashboard values:

```text
Status: Charging
Battery: 100 %
Mowing progress: 74 %
Mowed area: 160 m²
Cutting height: 40 mm
Wi-Fi signal: -74 dBm
```

---

## 🛣️ Roadmap

Planned or possible improvements:

- Better error code descriptions
- Improved diagnostics
- More confirmed Handwise models
- Optional path / route visualization
- Better translations
- More automation examples
- Enhanced HACS release structure

---

## 🤝 Contributing

Contributions are welcome.

You can help by:

- Testing additional Handwise mower models
- Reporting bugs
- Sharing diagnostic data
- Improving translations
- Creating pull requests
- Opening feature requests

If you test another model, please include:

- Mower model
- Firmware version if available
- Working entities
- Non-working entities
- Relevant Home Assistant logs

---

## ⚠️ Disclaimer

Handwise-HA is an independent community project.

This project is not affiliated with, endorsed by, maintained by, or supported by Handwise or Anthbot.

Use this integration at your own risk.

---

# Deutsch

## ✨ Funktionen

Handwise-HA unterstützt aktuell:

- 🌿 Native Home-Assistant-Mähroboter-Entität
- ▶️ Mähen starten
- ⏸️ Mähen pausieren
- 🏠 Zur Ladestation zurückkehren
- 🔋 Akkustand
- 📡 Verbindungsstatus
- 🔌 Ladezustand
- 📊 Mähfortschritt
- 📐 Gemähte Fläche
- ✂️ Schnitthöhe
- 📶 WLAN-Signalstärke
- ⚠️ Fehlercode
- 🌧️ Regenerkennung
- 🔐 PIN-/Sperrstatus
- 🧪 Diagnose-Sensoren
- 🗺️ Aktuelle Pfaddaten als Diagnosewert

---

## ✅ Unterstützte Modelle

### Erfolgreich getestet

| Marke | Modell | Status |
|---|---|---|
| Handwise | MGC01 500 | ✅ Getestet |

### Wahrscheinlich kompatibel

Diese Integration könnte auch mit weiteren Handwise-Mährobotern funktionieren, die dieselbe Handwise-/Anthbot-Cloud-Plattform verwenden.

Mögliche Kandidaten:

- Weitere Handwise-Mähroboter
- Anthbot-Genie-basierte Mähroboter
- Zukünftige cloudfähige Handwise-Modelle

Wenn dein Mähroboter mit der **Handwise**- oder **Anthbot**-App funktioniert, besteht eine Chance, dass er auch mit dieser Integration funktioniert.

Bitte erstelle ein Issue, wenn du ein weiteres Modell erfolgreich getestet hast.

---

## 📦 Installation

### Installation über HACS

1. **HACS** öffnen
2. Zu **Integrationen** wechseln
3. Oben rechts das Menü öffnen
4. **Benutzerdefinierte Repositories** auswählen
5. Diese Repository-URL eintragen:

```text
https://github.com/MTTPoll/handwise-ha
```

6. Kategorie auswählen:

```text
Integration
```

7. **Handwise-HA** installieren
8. Home Assistant neu starten

---

### Manuelle Installation

Diesen Ordner kopieren:

```text
custom_components/handwise_ha
```

nach:

```text
config/custom_components/handwise_ha
```

Danach Home Assistant neu starten.

---

## ⚙️ Einrichtung

Nach der Installation:

1. Home Assistant öffnen
2. Zu folgendem Menü wechseln:

```text
Einstellungen → Geräte & Dienste → Integration hinzufügen
```

3. Nach folgender Integration suchen:

```text
Handwise-HA
```

4. Handwise-Zugangsdaten eingeben
5. Mähroboter auswählen
6. Einrichtung abschließen

---

## 🧩 Verfügbare Entitäten

Die tatsächlich verfügbaren Entitäten können je nach Modell und Firmware abweichen.

### Mähroboter

- Mähroboter-Steuerung
- Mähen starten
- Mähen pausieren
- Zur Ladestation zurückkehren

### Sensoren

- Akkustand
- Mäherstatus
- Mähfortschritt
- Gemähte Fläche
- Schnitthöhe
- WLAN-Signal
- Fehlercode
- Ereigniscode
- IP-Adresse
- PIN-Status
- Regenstatus
- Regen-Wartezeit
- Firmware-Informationen
- Aktuelle Pfaddaten als Diagnosewert

### Binärsensoren

- Verbindung
- Ladevorgang
- Regenerkennung
- Fehlerstatus
- Sicherheitsauslösung

### Steuerungen

- Schnitthöhe
- Regenerkennung
- Regen-Wartezeit

---

## 🧪 Diagnose

Handwise-HA enthält zusätzliche Diagnose-Entitäten, die bei Fehlersuche und Weiterentwicklung helfen können.

Beispiele:

- Fehlercode
- Ereigniscode
- WLAN-Signal
- Firmware-Versionen
- Aktuelle Pfaddaten
- Interner Mäherstatus

Die aktuellen Pfaddaten werden momentan nur als Diagnosewert bereitgestellt. Eine Karten- oder Routenanzeige kann später ergänzt werden.

---

## 🏡 Dashboard-Ideen

Handwise-HA funktioniert mit normalen Home-Assistant-Dashboard-Karten.

Empfohlene Karten:

- Kachelkarte
- Entitäten-Karte
- Mushroom Cards
- Eigene Dashboard-Karten

Beispielwerte im Dashboard:

```text
Status: Laden
Akku: 100 %
Mähfortschritt: 74 %
Gemähte Fläche: 160 m²
Schnitthöhe: 40 mm
WLAN-Signal: -74 dBm
```

---

## 🛣️ Roadmap

Geplante oder mögliche Verbesserungen:

- Bessere Beschreibung der Fehlercodes
- Erweiterte Diagnosefunktionen
- Weitere bestätigte Handwise-Modelle
- Optionale Pfad-/Routenanzeige
- Bessere Übersetzungen
- Mehr Automationsbeispiele
- Verbesserte HACS-Release-Struktur

---

## 🤝 Mitwirken

Beiträge sind willkommen.

Du kannst helfen durch:

- Tests mit weiteren Handwise-Modellen
- Fehlermeldungen
- Teilen von Diagnoseinformationen
- Verbesserung von Übersetzungen
- Pull Requests
- Feature-Wünsche

Wenn du ein weiteres Modell testest, gib bitte möglichst Folgendes an:

- Mähermodell
- Firmware-Version, falls verfügbar
- Funktionierende Entitäten
- Nicht funktionierende Entitäten
- Relevante Home-Assistant-Logs

---

## ⚠️ Haftungsausschluss

Handwise-HA ist ein unabhängiges Community-Projekt.

Dieses Projekt steht in keiner Verbindung zu Handwise oder Anthbot und wird weder von Handwise noch von Anthbot unterstützt, gepflegt oder empfohlen.

Die Nutzung erfolgt auf eigene Verantwortung.
