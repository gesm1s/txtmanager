# TxtManager 🔤

A macOS text replacement manager that reads and writes directly to the system database — no export/import required.

Built by reverse-engineering the undocumented `KeyboardServices/TextReplacements.db` storage format introduced in macOS 15/26.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![macOS](https://img.shields.io/badge/macOS-15%2B%20%2F%2026-blue)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Features

- 📋 View all your text replacements in a clean GUI
- ➕ Add new shortcuts and phrases
- ✏️ Edit existing entries with double-click
- 🗑 Delete entries instantly
- 🔄 Find and replace text across all phrases at once
- 🔍 Auto-detects repeated values across phrases for batch updating (e.g. version numbers, device names)
- 💾 Writes directly to macOS — changes are active immediately
- ☁️ Syncs automatically to iPhone/iPad via iCloud/CloudKit
- 🔒 Creates a timestamped backup before every save

---

## Requirements

- macOS 15 (Sequoia) or macOS 26 and later
- Python 3.10 or later

> **Note:** This tool does **not** work on macOS 14 (Sonoma) or earlier, as Apple moved text replacements to a new SQLite-based storage format in macOS 15.

---

## Installation

1. Clone the repository:
```bash
git clone https://github.com/gesm1s/txtmanager.git
cd txtmanager
```

2. Run the app:
```bash
python3 teksterstatning_gui.py
```

---

## Optional: Create a clickable app

You can package TxtManager as a double-clickable macOS app:

```bash
mkdir -p ~/Applications/Txtmanager.app/Contents/MacOS
cp teksterstatning_gui.py ~/Applications/Txtmanager.app/Contents/MacOS/

cat > ~/Applications/Txtmanager.app/Contents/MacOS/run << 'EOF'
#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 "$DIR/teksterstatning_gui.py"
EOF

chmod +x ~/Applications/Txtmanager.app/Contents/MacOS/run
```

> Adjust the Python path to match your installation (`which python3`).

An app icon (`txtmanager.svg`) is included. Convert it to PNG with:
```bash
qlmanage -t -s 1024 -o ~/Desktop ~/Desktop/txtmanager.svg
```
Then paste it onto the app via **Get Info** (Cmd+I).

---

## How it works

Apple stores text replacements in a SQLite database at:

```
~/Library/KeyboardServices/TextReplacements.db
```

TxtManager reads and writes directly to this database using the `ZTEXTREPLACEMENTENTRY` table. After each change, it restarts `keyboardservicesd` so changes take effect immediately without restarting your Mac.

Changes are picked up by iCloud and synced to all your Apple devices automatically.

### Database schema

| Column | Description |
|---|---|
| `ZSHORTCUT` | The abbreviation you type |
| `ZPHRASE` | The text it expands to |
| `ZTIMESTAMP` | CoreData timestamp (seconds since 2001-01-01) |
| `ZNEEDSSAVETOCLOUD` | 1 = pending sync to iCloud |
| `ZWASDELETED` | Soft delete flag |
| `ZUNIQUENAME` | UUID used as CloudKit record ID |

---

## Batch update

The **Repeated values** panel on the right automatically detects any text that appears in two or more phrases — version numbers, device names, email addresses, etc. Double-click any value to replace it everywhere at once.

This is especially useful for QA documentation where you need to update things like:

- `Arena Mobil versjon 4.50.31` → `Arena Mobil versjon 4.51.0`
- `iPhone 16e (iOS 26.3)` → `iPhone 16e (iOS 26.4)`

---

## Backups

A timestamped backup of the database is created automatically before every change:

```
~/Library/KeyboardServices/TextReplacements.db.backup_20260305_143022
```

---

## Disclaimer

This tool accesses an undocumented internal macOS database. While it works reliably on macOS 15/26, future macOS updates may change the storage format. Always keep backups.

---

## License

MIT — free to use, modify and distribute.
