#!/bin/bash
# Txtmanager — installasjonsscript
# Kjør med: bash install.sh
# Krever at Txtmanager.app er pakket ut i samme mappe som dette scriptet
#
# VIKTIG — bygg alltid via GitHub Actions CI, ikke lokalt med py2app:
# Lokal bygg med CommandLineTools Python 3.9 produserer feil rpath i den bundlede
# python-binæren (@executable_path/../../../../Python3 → /Python3 finnes ikke).
# CI bruker Python 3.12 og produserer korrekt rpath (@executable_path/../Frameworks/...).
# Last alltid ned fra https://github.com/gesm1s/txtmanager/releases — ikke bygg selv.

set -e

APP_NAME="Txtmanager.app"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC="$SCRIPT_DIR/$APP_NAME"
DEST="/Applications/$APP_NAME"

if [ ! -d "$SRC" ]; then
    echo "Feil: Finner ikke $APP_NAME i samme mappe som scriptet."
    echo "Pass på at du har pakket ut ZIP-filen og kjører install.sh derfra."
    exit 1
fi

echo "Installerer $APP_NAME..."
rm -rf "$DEST"
ditto "$SRC" "$DEST"
xattr -cr "$DEST"
echo "Ferdig! Start Txtmanager fra Launchpad eller Finder → Programmer."
