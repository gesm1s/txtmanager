# Changelog

All notable changes to Txtmanager are documented here.

## [Unreleased]

No user-facing changes since v1.4.2.

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

[Unreleased]: https://github.com/gesm1s/txtmanager/compare/v1.4.2...HEAD
[1.4.2]: https://github.com/gesm1s/txtmanager/compare/v1.4.1...v1.4.2
[1.4.1]: https://github.com/gesm1s/txtmanager/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/gesm1s/txtmanager/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/gesm1s/txtmanager/compare/v1.1.1...v1.3.0
[1.1.1]: https://github.com/gesm1s/txtmanager/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/gesm1s/txtmanager/compare/v1.0.2...v1.1.0
[1.0.2]: https://github.com/gesm1s/txtmanager/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/gesm1s/txtmanager/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/gesm1s/txtmanager/releases/tag/v1.0.0
