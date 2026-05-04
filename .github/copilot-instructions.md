# Copilot Instructions for txtmanager

## GitHub Actions Workflow – Signering

> **VIKTIG:** Signing og notarization er midlertidig **deaktivert** i `.github/workflows/build.yml`.
>
> Stegene `Import signing certificate`, `Sign app`, `Notarize app` og `Staple notarization` er kommentert ut.
>
> **Aktiver dem igjen når følgende GitHub Secrets er satt opp:**
> - `MACOS_CERTIFICATE` – Base64-kodet .p12 sertifikat
> - `MACOS_CERTIFICATE_PWD` – Passord til sertifikatet
> - `KEYCHAIN_PASSWORD` – Valgfritt passord for midlertidig keychain
> - `APPLE_SIGN_IDENTITY` – f.eks. `Developer ID Application: Navn (TEAMID)`
> - `APPLE_ID` – Apple-ID brukt for notarization
> - `APPLE_APP_SPECIFIC_PASSWORD` – App-spesifikt passord fra appleid.apple.com
> - `APPLE_TEAM_ID` – Apple Developer Team ID

## Oppdatering av appen

Når du installerer en ny versjon av Txtmanager.app, **må tilgjengelighets-tillatelsen fjernes først**
(Systeminnstillinger → Personvern og sikkerhet → Tilgjengelighet → fjern Txtmanager),
og deretter legges til på nytt etter installasjon. Ellers feiler synkroniseringen.
