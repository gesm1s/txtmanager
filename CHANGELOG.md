# Changelog

All notable changes to Txtmanager are documented here.

## [Unreleased]

No user-facing changes since v1.4.8.

## [1.4.8] – 2026-05-27

### Added
- «Oppdater nå»-knapp i oppdateringsbanneret: laster ned ZIP fra GitHub Releases, pakker ut, installerer med `ditto` + `xattr -cr`, og starter appen på nytt automatisk. Fremdrift vises i banneret (%, pakker ut, installerer, starter på nytt).

## [1.4.7] – 2026-05-27

### Changed
- Oppdateringsvarsel vises nå som en gul banner øverst i vinduet (ikke i statuslinjen) med «Last ned →»-knapp som åpner GitHub Releases direkte. Banneren lukkes med ✕.

## [1.4.6] – 2026-05-22

### Fixed
- `sys.exit(1)` i XPC-skriptet avslutter ikke prosessen i PyObjC/NSRunLoop-konteksten — utføringen fortsetter til den siste `try: os.unlink` som er stille, og prosessen avslutter med kode 0. Ytre kode trodde synkroniseringen gikk bra mens XPC faktisk hadde timeout. Erstattet med `os._exit(1)` som kaller C-laget direkte og ikke kan fanges av PyObjC.

## [1.4.5] – 2026-05-22

### Fixed
- `FileNotFoundError` i XPC-skriptet ved `os.unlink(data_path)` på siste linje: `sys.exit(1)` avslutter ikke alltid prosessen i PyObjC-kjøreloopkontekst, og filen var allerede slettet av timeout-stien. Pakket inn i `try/except OSError`.

## [1.4.4] – 2026-05-22

### Fixed
- XPC-sync feilet alltid med `UnicodeEncodeError` i app-bundle-miljøet fordi `open()` ble kalt uten `encoding="utf-8"`. Alle synkroniseringer har feilet siden v1.4.3 — dette er årsaken til sporadiske reverteringer. Fikset ved eksplisitt UTF-8 på alle relevante filoperasjoner og `PYTHONUTF8=1` i subprocess-miljøet.

## [1.4.3] – 2026-05-12

### Added
- Versjon og byggedato vises øverst til høyre i vinduet
- «Verktøy»-meny med snarveier til loggfil (åpne i Console, vis i Finder)

### Fixed
- Stille sync-feil ved oppstart: XPC-scriptet returnerer nå feil ved intern timeout, slik at retry-mekanismen trigges korrekt
- Loggfilen fikk ikke oppføringer ved sync-feil etter v1.4.2
- Midlertidig datafil i `/tmp` ble ikke ryddet opp ved XPC-timeout

### Changed
- Retry-forsinkelser samlet i én konstant (`_SYNC_RETRY_DELAYS`) i stedet for duplisert i to steder

### Removed
- Død kode: ubrukt variabel `desired_shortcuts` i XPC-sync-skriptet

## [1.4.2] – 2026-05-04

### Added
- Sjekker GitHub for oppdateringer ved oppstart og viser status i menylinjen

### Fixed
- Retry med backoff ved sync for å håndtere race condition mot `keyboardservicesd` ved innlogging

## [1.4.1] – 2026-04-29

### Fixed
- Stille sync-feil ble ikke fanget opp og rapportert
- Backups flyttes til dedikert mappe
- Logging forbedret

## [1.4.0] – 2026-04-27

### Changed
- Bruker nå KeyboardServices XPC API for umiddelbar sync til alle apper uten krav om omstart

## [1.3.0] – 2026-04-22

### Fixed
- Teksterstattning ble ikke propagert korrekt til åpne apper

## [1.1.1] – 2026-04-12

### Improved
- Bedre finn/erstatt UX
- Lagring verifiseres etter skriving

## [1.1.0] – 2026-04-08

### Fixed
- WAL checkpoint sikrer at `keyboardservicesd` leser oppdatert data
- Lagt til `xattr`-fjerning i installasjonsinstruksjoner for å unngå karanteneproblemer

## [1.0.2] – 2026-03-16

### Fixed
- Fallback til siste backup fungerte ikke i alle tilfeller

## [1.0.1] – 2026-03-12

### Fixed
- Rekkefølge på daemon-dreping ved avslutning
- py2app-bygg lagt til

## [1.0.0] – 2026-03-05

### Added
- Første release
- Tospråklig støtte (norsk/engelsk)
- Ikon

[Unreleased]: https://github.com/gesm1s/txtmanager/compare/v1.4.8...HEAD
[1.4.8]: https://github.com/gesm1s/txtmanager/compare/v1.4.7...v1.4.8
[1.4.7]: https://github.com/gesm1s/txtmanager/compare/v1.4.6...v1.4.7
[1.4.6]: https://github.com/gesm1s/txtmanager/compare/v1.4.5...v1.4.6
[1.4.5]: https://github.com/gesm1s/txtmanager/compare/v1.4.4...v1.4.5
[1.4.4]: https://github.com/gesm1s/txtmanager/compare/v1.4.3...v1.4.4
[1.4.3]: https://github.com/gesm1s/txtmanager/compare/v1.4.2...v1.4.3
[1.4.2]: https://github.com/gesm1s/txtmanager/compare/v1.4.1...v1.4.2
[1.4.1]: https://github.com/gesm1s/txtmanager/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/gesm1s/txtmanager/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/gesm1s/txtmanager/compare/v1.1.1...v1.3.0
[1.1.1]: https://github.com/gesm1s/txtmanager/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/gesm1s/txtmanager/compare/v1.0.2...v1.1.0
[1.0.2]: https://github.com/gesm1s/txtmanager/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/gesm1s/txtmanager/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/gesm1s/txtmanager/releases/tag/v1.0.0
