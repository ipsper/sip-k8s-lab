# Felsökningar Bibliotek

Detta bibliotek innehåller dokumentation av felsökningar för SIPp K8s Lab projektet.

## Struktur

```
felsökningar/
├── README.md                    # Denna fil
├── 2025-07-31/                 # Dagens felsökning
│   └── README.md               # test_options_scenario timeout
└── [datum]/                    # Framtida felsökningar
    └── README.md
```

## Felsökningar

### 2025-07-31 - test_options_scenario timeout
**Problem:** SIPp-testet fick timeout och misslyckades  
**Status:** Delvis löst - Docker image och tm module problem fixade  
**Läs mer:** [2025-07-31/README.md](2025-07-31/README.md)

## Mall för nya felsökningar

När du skapar en ny felsökning, använd följande struktur:

```markdown
# Felsökning: [Problemnamn]

**Datum:** YYYY-MM-DD  
**Problem:** [Kort beskrivning]

## Problembeskrivning
[Detaljerad beskrivning av problemet]

## Rotorsaksanalys
[Analys av vad som orsakade problemet]

## Lösning
[Steg för steg lösning]

## Resultat
[Vad som blev löst och vad som kvarstår]

## Lärdomar
[Vad vi lärde oss av detta]

## Filer Ändrade
[Lista över ändrade filer]
```

## Kommandon för att skapa ny felsökning

```bash
# Skapa ny felsökning för idag
mkdir -p felsökningar/$(date +%Y-%m-%d)
touch felsökningar/$(date +%Y-%m-%d)/README.md

# Uppdatera denna index-fil
# Lägg till länk till nya felsökningen
``` 