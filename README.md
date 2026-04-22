# TxtManager 🔤

A macOS text replacement manager that reads and writes directly to the system database — no export/import required.

Built by reverse-engineering the undocumented `KeyboardServices/TextReplacements.db` storage format introduced in macOS 15/26.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![macOS](https://img.shields.io/badge/macOS-15%2B%20%2F%2026-blue)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Features

- 📋 View all your text replacements in a clean GUI
- 🇳🇴/🇬🇧 Supports norwegian and english
- ➕ Add new shortcuts and phrases
- ✏️ Edit existing entries with double-click
- 🗑 Delete entries instantly
- 🔄 Find and replace text across all phrases at once
- 🔎 Live preview while typing in Find & Replace (the main list filters instantly)
- 🔍 Auto-detects repeated values across phrases for batch updating (e.g. version numbers, device names)
- 🖱 Click repeated values to edit directly in the side panel and apply replacement immediately
- 🛡 Post-save verification warns if an update appears to be overwritten by sync/daemon state
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

### Download the app (recommended)

1. Download `Txtmanager.app.zip` from the [latest release](https://github.com/gesm1s/txtmanager/releases/latest)
2. Unzip and move `Txtmanager.app` to `/Applications/`
3. Remove the macOS quarantine flag (required because the app is not signed with an Apple Developer certificate):
```bash
xattr -cr /Applications/Txtmanager.app
```
4. Launch from Finder or Launchpad

### Run from source

1. Clone the repository:
```bash
git clone https://github.com/gesm1s/txtmanager.git
cd txtmanager
```

2. Run:
```bash
python3 teksterstatning_gui.py
```

### Build the app yourself

Requires [py2app](https://py2app.readthedocs.io/):

```bash
pip3 install py2app
python3 setup.py py2app
cp -R dist/Txtmanager.app /Applications/
```

---

## How to use

1. Launch Txtmanager
2. Your existing macOS text replacements are loaded automatically
3. **Add**: Click **+ Ny snarvei** / **+ New shortcut** to add a new entry
4. **Edit**: Double-click any row to edit shortcut or phrase
5. **Delete**: Select a row and click **🗑 Slett** / **🗑 Delete**
6. **Find & Replace**: Click the button to search and replace across all phrases — the main list filters live as you type
7. **Version Bump**: Click **🔢 Versjonsoppdatering** to auto-detect version numbers across your phrases and update them in one click
8. **Repeated values** (right panel): Click any value that appears in multiple phrases to edit and replace it instantly

Changes are saved directly to macOS and propagated to all apps (Safari, Chrome, Slack, etc.) within seconds. iCloud syncs changes to your iPhone/iPad automatically.

---

## How it works

Apple stores text replacements in a SQLite database at:

```
~/Library/KeyboardServices/TextReplacements.db
```

TxtManager reads and writes directly to this database using the `ZTEXTREPLACEMENTENTRY` table. After each change, it performs a WAL checkpoint to ensure all data is written to the main database file, then stops `keyboardservicesd` so the daemon restarts with the updated data — no reboot required.

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

The **Repeated values** panel on the right automatically detects any text that appears in two or more phrases — version numbers, device names, email addresses, etc.

You can now:

- Click a value to select it
- Edit it directly in the right-side input field
- Press **Replace selected expression** (or Enter) to update all matching phrases

This is especially useful for QA documentation where you need to update things like:

- `Arena Mobil versjon 4.50.31` → `Arena Mobil versjon 4.51.0`
- `iPhone 16e (iOS 26.3)` → `iPhone 16e (iOS 26.4)`

## Find & Replace live preview

When opening **Find & Replace**, typing in the **Find** field now:

- Filters the main shortcut list live
- Shows a running match counter (`Matches: X`)
- Restores your original list filter when the dialog is closed

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
