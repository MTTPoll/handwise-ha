# Handwise-HA

Home Assistant integration for Handwise robotic lawn mowers.

Handwise-HA integrates Handwise robotic lawn mowers directly into Home Assistant and provides monitoring, diagnostics, and control capabilities through the Anthbot/Handwise cloud platform.

---

## Features

✅ Battery level monitoring

✅ Mower status and activity

✅ Charging status

✅ Mowing progress

✅ Mowed area statistics

✅ Cutting height monitoring

✅ Wi-Fi signal strength

✅ Error code reporting

✅ Rain detection settings

✅ Start mowing

✅ Stop mowing

✅ Return to charging station

✅ Diagnostic entities

✅ Native Home Assistant Lawn Mower support

---

## Supported Models

### Confirmed

* Handwise MGC01 500

### Potentially Compatible

This integration is designed for Handwise robotic lawn mowers using the Anthbot cloud platform and may also work with:

* Other Handwise robotic mower models
* Anthbot Genie models
* Future Handwise cloud-connected mower models

If your mower is managed through the Handwise or Anthbot mobile application, there is a good chance it is compatible.

Please report successful tests with additional models.

---

## Installation

### HACS (Recommended)

1. Open HACS
2. Navigate to **Integrations**
3. Open the menu and select **Custom repositories**
4. Add:

```text
https://github.com/MTTPoll/handwise-ha
```

5. Select category:

```text
Integration
```

6. Install **Handwise-HA**
7. Restart Home Assistant

---

### Manual Installation

Copy the folder:

```text
custom_components/handwise_ha
```

to:

```text
config/custom_components/handwise_ha
```

Restart Home Assistant afterwards.

---

## Configuration

1. Open Home Assistant
2. Navigate to:

```text
Settings → Devices & Services → Add Integration
```

3. Search for:

```text
Handwise-HA
```

4. Enter your Handwise account credentials
5. Complete setup

---

## Available Entities

Depending on the mower model, the following entities may be available:

### Lawn Mower

* Lawn mower control entity
* Start mowing
* Stop mowing
* Return to dock

### Sensors

* Battery level
* Mower status
* Mowing progress
* Mowed area
* Cutting height
* Wi-Fi signal
* Error code
* IP address
* Diagnostic sensors

### Binary Sensors

* Connectivity
* Charging
* Rain detection
* Safety state

### Controls

* Rain detection
* Cutting height
* Mowing parameters

---

## Diagnostics

Handwise-HA exposes additional diagnostic information to help troubleshoot mower operation and cloud communication.

Examples include:

* Error codes
* Wi-Fi signal quality
* Connection state
* Firmware information
* Internal mower status information

---

## Home Assistant Dashboard

The integration is designed to work with standard Home Assistant dashboard cards and can be combined with:

* Mushroom Cards
* Tile Cards
* Entities Cards
* Custom Mower Dashboards

---

## Roadmap

Planned improvements:

* Route visualization
* Mowing path analysis
* Map support
* Additional mower diagnostics
* Enhanced automation support
* Support for additional Handwise models

---

## Contributing

Contributions, bug reports, feature requests and testing feedback are always welcome.

If you own a Handwise mower that is not yet listed as supported, please open an issue and provide details about your model.

---

## Disclaimer

Handwise-HA is an independent community project.

This project is not affiliated with, endorsed by, or supported by Handwise or Anthbot.

---

# Deutsch

## Handwise-HA

Home-Assistant-Integration für Handwise Mähroboter.

Handwise-HA integriert Handwise-Mähroboter direkt in Home Assistant und ermöglicht Überwachung, Diagnose und Steuerung über die Handwise-/Anthbot-Cloud.

---

## Funktionen

✅ Akkustand

✅ Mäherstatus

✅ Ladezustand

✅ Mähfortschritt

✅ Gemähte Fläche

✅ Schnitthöhe

✅ WLAN-Signalstärke

✅ Fehlercodes

✅ Regenerkennung

✅ Mähen starten

✅ Mähen stoppen

✅ Zur Ladestation zurückkehren

✅ Diagnose-Entitäten

✅ Native Home-Assistant-Mähroboter-Unterstützung

---

## Unterstützte Modelle

### Bestätigt

* Handwise MGC01 500

### Wahrscheinlich kompatibel

Diese Integration wurde für Handwise-Mähroboter entwickelt, die die Anthbot-Cloud-Plattform verwenden, und könnte ebenfalls mit folgenden Modellen funktionieren:

* Weitere Handwise-Mähroboter
* Anthbot-Genie-Modelle
* Zukünftige Handwise-Modelle mit Cloud-Anbindung

Wenn dein Mähroboter über die Handwise- oder Anthbot-App verwaltet wird, besteht eine gute Chance, dass er kompatibel ist.

Bitte melde erfolgreiche Tests mit weiteren Modellen.

---

## Installation

### HACS (Empfohlen)

Repository hinzufügen:

```text
https://github.com/MTTPoll/handwise-ha
```

Kategorie:

```text
Integration
```

Anschließend Handwise-HA installieren und Home Assistant neu starten.

---

### Manuelle Installation

Den Ordner:

```text
custom_components/handwise_ha
```

nach:

```text
config/custom_components/handwise_ha
```

kopieren.

Danach Home Assistant neu starten.

---

## Verfügbare Entitäten

Je nach Modell:

### Mähroboter

* Mähroboter-Steuerung
* Mähen starten
* Mähen stoppen
* Zur Ladestation fahren

### Sensoren

* Akkustand
* Mäherstatus
* Mähfortschritt
* Mähfläche
* Schnitthöhe
* WLAN-Signal
* Fehlercode
* IP-Adresse
* Diagnose-Sensoren

### Binärsensoren

* Verbindung
* Laden
* Regenerkennung
* Sicherheitsstatus

### Steuerungen

* Regenerkennung
* Schnitthöhe
* Mähparameter

---

## Geplante Funktionen

* Routenanzeige
* Visualisierung der Fahrspur
* Kartenunterstützung
* Erweiterte Diagnosefunktionen
* Unterstützung weiterer Handwise-Modelle

---

## Mitwirken

Fehlerberichte, Pull Requests und Testergebnisse sind jederzeit willkommen.

Besitzer weiterer Handwise-Modelle sind ausdrücklich eingeladen, die Kompatibilität zu testen und Rückmeldung zu geben.

---

## Haftungsausschluss

Handwise-HA ist ein unabhängiges Community-Projekt.

Es besteht keine Verbindung zu Handwise oder Anthbot.
