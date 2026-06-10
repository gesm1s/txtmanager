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
- 💾 Writes directly to macOS — changes are active immediately in all apps
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
2. Unzip the archive
3. Install and remove the macOS quarantine flag in one step (required — Finder drag-and-drop adds quarantine which silently breaks sync):
```bash
rm -rf /Applications/Txtmanager.app
ditto ~/Downloads/Txtmanager.app /Applications/Txtmanager.app
xattr -cr /Applications/Txtmanager.app
```
4. Launch from Finder or Launchpad

> **Important:** Do **not** copy the app using Finder drag-and-drop. macOS adds a quarantine flag to unsigned apps copied with Finder, which silently prevents the sync script from running. Always install using the Terminal commands above.

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

Changes are saved directly to macOS and propagated to all apps (Safari, Slack, Outlook, etc.) immediately. iCloud syncs changes to your iPhone/iPad automatically.

---

## How it works

Apple stores text replacements in a SQLite database at:

```
~/Library/KeyboardServices/TextReplacements.db
```

TxtManager reads and writes directly to this database using the `ZTEXTREPLACEMENTENTRY` table. After each change, it performs a WAL checkpoint to flush all data to the main database file.

### Propagating changes to running apps

macOS uses two separate mechanisms to deliver text replacements to apps:

| App type | Mechanism |
|---|---|
| NSTextView apps (TextEdit, Notes, etc.) | Read from `NSUserDictionaryReplacementItems` in `NSGlobalDomain` plist; notified via `NSSpellCheckerDidChangeAutomaticTextReplacementNotification` |
| XPC-connected apps (Safari, Slack, Outlook) | Receive push updates from `keyboardservicesd` via a private XPC service |

To handle both, TxtManager:

1. **Writes to the SQLite database** (source of truth for all storage and iCloud sync)
2. **Updates `NSUserDictionaryReplacementItems`** and sends `NSSpellCheckerDidChangeAutomaticTextReplacementNotification` (for TextEdit and similar apps)
3. **Calls the private `_KSTextReplacementClientStore` XPC API** from `KeyboardServices.framework` — the same API used internally by System Settings — to push changes directly to `keyboardservicesd`, which immediately notifies Safari, Slack, Outlook and other XPC-connected apps. Each operation is dispatched as a typed XPC call: `modifyEntry:toEntry:withCompletionHandler:` for edits (matched on shortcut + phrase), `addEntries:removeEntries:` for inserts and deletions. This updates keyboardservicesd's in-memory state directly without reading current entries first, which avoids the conflict where keyboardservicesd's CloudKit-backed state would otherwise overwrite the DB write within seconds.

> **Why not just restart `keyboardservicesd`?**
> Earlier versions of TxtManager restarted the `keyboardservicesd` daemon after a DB write. This worked initially but broke in later macOS 15.x/26 updates: restarting the daemon causes it to re-sync from iCloud (CloudKit), which can overwrite local changes with stale values from other devices. It also disrupts XPC connections in running apps, causing reconnect delays of several minutes. Using the op-based XPC client API avoids all of these issues.

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

A timestamped backup of the database is created automatically before every change, stored in a dedicated directory:

```
~/Library/Application Support/TxtManager/backups/TextReplacements.db.backup_20260429_112200
```

At most **10 backups** are kept — older ones are deleted automatically.

---

## Logging

TxtManager writes its operational log to:

```
~/Library/Logs/TxtManager.log
```

The log includes backup creation, version bump requests, DB updates, XPC sync attempts/results, and immediate/delayed save verification. This makes it easier to diagnose cases where the SQLite database is correct but `keyboardservicesd`, CloudKit, or a running app temporarily keeps an older replacement in memory. The file rotates automatically when it grows.

You can view it in **Console.app** (search for "TxtManager") or in Terminal:

```bash
cat ~/Library/Logs/TxtManager.log
```

If an XPC operation times out, TxtManager retries once after 10 seconds. If that also fails, the DB write remains the source of truth and keyboardservicesd will eventually pick up the change via its own file-watch mechanism.

If the app itself crashes, macOS writes crash reports under:

```
~/Library/Logs/DiagnosticReports/Txtmanager_*.crash
~/Library/Logs/DiagnosticReports/Txtmanager_*.ips
```

---

## Disclaimer

This tool accesses an undocumented internal macOS database and a private system framework (`KeyboardServices.framework`). While it works reliably on macOS 15/26, future macOS updates may change the storage format or private APIs. Always keep backups.

---

## License

MIT — free to use, modify and distribute.
