#!/usr/bin/env python3
"""
TxtManager 1.4.8 for macOS 15+/26
- Reads/writes directly to ~/Library/KeyboardServices/TextReplacements.db
- No export/import needed
- Syncs automatically to iPhone/iPad via iCloud/CloudKit
- Bilingual: Norwegian / English (follows macOS language setting)
"""

import sys, sqlite3, time, uuid, subprocess, os, re, shutil, locale, threading
from collections import Counter
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

# ── Language detection ─────────────────────────────────────────────────────────
def _detect_lang():
    # 1. Check standard env vars
    lang = os.environ.get("LANG", "") or os.environ.get("LANGUAGE", "") or locale.getlocale()[0] or ""
    if any(lang.startswith(x) for x in ("nb", "nn", "no")):
        return "no"
    # 2. On macOS, check AppleLanguages (the actual system language setting)
    try:
        r = subprocess.run(["defaults", "read", "NSGlobalDomain", "AppleLanguages"],
                           capture_output=True, text=True, timeout=2)
        if r.returncode == 0 and any(x in r.stdout for x in ("nb", "nn", "no")):
            return "no"
    except Exception:
        pass
    return "en"

LANG = _detect_lang()

T = {
    "title":              {"no": "Teksterstatning Manager", "en": "Text Replacement Manager"},
    "col_shortcut":       {"no": "Snarvei",                "en": "Shortcut"},
    "col_phrase":         {"no": "Frase",                  "en": "Phrase"},
    "btn_new":            {"no": "➕ Ny",                  "en": "➕ New"},
    "btn_edit":           {"no": "✏️  Endre",               "en": "✏️  Edit"},
    "btn_delete":         {"no": "🗑  Slett",               "en": "🗑  Delete"},
    "btn_findreplace":    {"no": "🔄 Finn/Erstatt",         "en": "🔄 Find/Replace"},
    "btn_reload":         {"no": "↺ Last inn på nytt",     "en": "↺ Reload"},
    "btn_update_list":    {"no": "↺ Oppdater liste",       "en": "↺ Refresh list"},
    "repeated_title":     {"no": "Gjentakende verdier",    "en": "Repeated values"},
    "repeated_hint":      {"no": "Dobbeltklikk for å erstatte i alle fraser",
                           "en": "Double-click to replace in all phrases"},
    "repeated_selected":  {"no": "Valgt uttrykk:",         "en": "Selected expression:"},
    "repeated_new_value": {"no": "Ny verdi:",              "en": "New value:"},
    "repeated_apply":     {"no": "Erstatt valgt uttrykk",  "en": "Replace selected expression"},
    "repeated_none":      {"no": "(ingen valgt)",          "en": "(none selected)"},
    "status_loaded":      {"no": "Lastet {n} snarveier direkte fra macOS.",
                           "en": "Loaded {n} shortcuts directly from macOS."},
    "status_added":       {"no": "✓ La til '{s}'.",        "en": "✓ Added '{s}'."},
    "status_edited":      {"no": "✓ Endret '{s}'.",        "en": "✓ Edited '{s}'."},
    "status_deleted":     {"no": "✓ Slettet '{s}'.",       "en": "✓ Deleted '{s}'."},
    "status_replaced":    {"no": "✓ Erstattet «{a}» → «{b}» i {n} fraser.",
                           "en": "✓ Replaced «{a}» → «{b}» in {n} phrases."},
    "status_findreplace": {"no": "✓ Finn/Erstatt: endret {n} fraser.",
                           "en": "✓ Find/Replace: changed {n} phrases."},
    "err_db":             {"no": "Kunne ikke lese databasen:\n{e}",
                           "en": "Could not read database:\n{e}"},
    "err_exists":         {"no": "'{s}' er allerede i bruk.", "en": "'{s}' already exists."},
    "err_exists_title":   {"no": "Finnes allerede",        "en": "Already exists"},
    "err_no_match":       {"no": "Fant ikke '{f}' i noen fraser.",
                           "en": "Could not find '{f}' in any phrases."},
    "err_no_match_title": {"no": "Ingen treff",            "en": "No matches"},
    "select_row":         {"no": "Klikk på en snarvei i lista først.",
                           "en": "Click a shortcut in the list first."},
    "select_row_title":   {"no": "Velg rad",               "en": "Select a row"},
    "confirm_delete":     {"no": "Slette snarveien '{s}'?","en": "Delete shortcut '{s}'?"},
    "confirm_title":      {"no": "Bekreft sletting",       "en": "Confirm deletion"},
    "dlg_new_title":      {"no": "Ny snarvei",             "en": "New shortcut"},
    "dlg_edit_title":     {"no": "Endre snarvei",          "en": "Edit shortcut"},
    "dlg_shortcut":       {"no": "Snarvei:",               "en": "Shortcut:"},
    "dlg_phrase":         {"no": "Frase:",                 "en": "Phrase:"},
    "dlg_save":           {"no": "Lagre",                  "en": "Save"},
    "dlg_cancel":         {"no": "Avbryt",                 "en": "Cancel"},
    "dlg_missing":        {"no": "Fyll ut begge felt.",    "en": "Please fill in both fields."},
    "dlg_missing_title":  {"no": "Mangler data",           "en": "Missing data"},
    "dlg_missing_val":    {"no": "Skriv inn ny verdi.",    "en": "Please enter a new value."},
    "dlg_missing_val_t":  {"no": "Mangler verdi",          "en": "Missing value"},
    "select_expression":  {"no": "Velg et uttrykk fra listen først.",
                             "en": "Select an expression from the list first."},
    "select_expression_t": {"no": "Velg uttrykk",           "en": "Select expression"},
    "batch_title":        {"no": "Oppdater alle forekomster", "en": "Update all occurrences"},
    "batch_replace":      {"no": "Erstatt ({n} fraser):",  "en": "Replace ({n} phrases):"},
    "batch_with":         {"no": "Med:",                   "en": "With:"},
    "batch_btn":          {"no": "Erstatt i alle fraser",  "en": "Replace in all phrases"},
    "find_title":         {"no": "Finn og erstatt",        "en": "Find and replace"},
    "find_label":         {"no": "Finn:",                  "en": "Find:"},
    "replace_label":      {"no": "Erstatt med:",           "en": "Replace with:"},
    "find_btn":           {"no": "Erstatt",                "en": "Replace"},
    "find_matches":       {"no": "Treff: {n}",             "en": "Matches: {n}"},
    "warn_sync_title":    {"no": "Mulig sync-konflikt",    "en": "Possible sync conflict"},
    "warn_sync_msg":      {"no": "Lagringen ser ut til å ha blitt overskrevet etter oppdatering.\n"
                                   "Prøv å lagre igjen, og vent noen sekunder før omstart/synk.",
                           "en": "The save appears to have been overwritten after update.\n"
                                   "Try saving again, and wait a few seconds before reboot/sync."},
    "btn_version_bump":   {"no": "🔢 Versjonsoppdatering", "en": "🔢 Version Bump"},
    "vb_title":           {"no": "Versjonsoppdatering",    "en": "Version Bump"},
    "vb_current":         {"no": "Nåværende versjon:",     "en": "Current version:"},
    "vb_new":             {"no": "Ny versjon:",            "en": "New version:"},
    "vb_affected":        {"no": "Berørte snarveier ({n}):", "en": "Affected shortcuts ({n}):"},
    "vb_apply":           {"no": "Oppdater alle",          "en": "Update all"},
    "vb_no_versions":     {"no": "Fant ingen versjonsnumre i snarveiene.", "en": "No version numbers found in shortcuts."},
    "vb_no_versions_t":   {"no": "Ingen versjoner",       "en": "No versions"},
    "vb_done":            {"no": "✓ Oppdaterte versjon «{a}» → «{b}» i {n} snarveier.",
                           "en": "✓ Updated version «{a}» → «{b}» in {n} shortcuts."},
    "update_available":   {"no": "Ny versjon tilgjengelig: {v}",
                           "en": "New version available: {v}"},
    "update_now":         {"no": "Oppdater nå",                 "en": "Update now"},
    "update_download":    {"no": "Mer info →",                  "en": "More info →"},
    "update_downloading": {"no": "⬇️  Laster ned v{v}...",      "en": "⬇️  Downloading v{v}..."},
    "update_extracting":  {"no": "📦  Pakker ut...",             "en": "📦  Extracting..."},
    "update_installing":  {"no": "🔧  Installerer...",           "en": "🔧  Installing..."},
    "update_restarting":  {"no": "✅  Ferdig! Starter på nytt...", "en": "✅  Done! Restarting..."},
    "update_error":       {"no": "❌  Feil: {e}",               "en": "❌  Error: {e}"},
    "version_label":      {"no": "v{v}  •  Bygget {b}",      "en": "v{v}  •  Built {b}"},
    "menu_tools":         {"no": "Verktøy",                   "en": "Tools"},
    "menu_open_log":      {"no": "Vis loggfil i Console",     "en": "Open log in Console"},
    "menu_reveal_log":    {"no": "Vis loggfil i Finder",      "en": "Reveal log in Finder"},
}

def t(key, **kwargs):
    text = T[key][LANG]
    return text.format(**kwargs) if kwargs else text

APP_VERSION = "1.4.14"

def _build_date():
    try:
        path = sys.executable if getattr(sys, "frozen", False) else __file__
        return datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d")
    except Exception:
        return "?"

APP_BUILD = _build_date()

GITHUB_RELEASES_API = "https://api.github.com/repos/gesm1s/txtmanager/releases/latest"

def _check_for_update(callback):
    """Fetch latest GitHub release tag in a background thread.
    Calls callback(latest_version) on the main thread if a newer version exists."""
    import urllib.request, json as _json
    def _fetch():
        try:
            req = urllib.request.Request(
                GITHUB_RELEASES_API,
                headers={"User-Agent": f"TxtManager/{APP_VERSION}"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = _json.loads(resp.read())
            tag = data.get("tag_name", "").lstrip("v")
            if tag and tag != APP_VERSION:
                # Compare as tuples to handle e.g. 1.4.2 > 1.4.1
                def _ver(s):
                    try: return tuple(int(x) for x in s.split("."))
                    except: return (0,)
                if _ver(tag) > _ver(APP_VERSION):
                    callback(tag)
        except Exception:
            pass  # silently ignore network errors
    threading.Thread(target=_fetch, daemon=True).start()

# ── Helpers ────────────────────────────────────────────────────────────────────
def _darken(hex_color):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"#{max(0,r-30):02x}{max(0,g-30):02x}{max(0,b-30):02x}"

def _normalize_shortcut(value):
    return (value or "").strip().lower()

# ── Config ─────────────────────────────────────────────────────────────────────
DB_PATH     = os.path.expanduser("~/Library/KeyboardServices/TextReplacements.db")
BACKUP_DIR  = os.path.expanduser("~/Library/Application Support/TxtManager/backups")
BACKUP_KEEP = 10
LOG_PATH    = os.path.expanduser("~/Library/Logs/TxtManager.log")
CD_EPOCH = 978307200
MIN_OCCURRENCES = 2

# ── Backend ────────────────────────────────────────────────────────────────────
def backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(DB_PATH, os.path.join(BACKUP_DIR, f"TextReplacements.db.backup_{ts}"))
    # Keep only the most recent BACKUP_KEEP backups
    existing = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.startswith("TextReplacements.db.backup_")],
        reverse=True
    )
    for old in existing[BACKUP_KEEP:]:
        try:
            os.remove(os.path.join(BACKUP_DIR, old))
        except OSError:
            pass

def get_conn():
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.execute("PRAGMA busy_timeout = 10000")
    return con

def _next_timestamp(con):
    now = time.time() - CD_EPOCH
    max_ts = con.execute("SELECT MAX(ZTIMESTAMP) FROM ZTEXTREPLACEMENTENTRY").fetchone()[0] or 0
    return max(now, max_ts + 0.001)

def wal_checkpoint():
    """Force WAL content into main database file so keyboardservicesd sees updates."""
    con = get_conn()
    con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    con.close()

def read_items():
    con = get_conn()
    rows = con.execute("""
        SELECT Z_PK, ZSHORTCUT, ZPHRASE
        FROM ZTEXTREPLACEMENTENTRY
        WHERE ZWASDELETED = 0
        ORDER BY ZSHORTCUT COLLATE NOCASE
    """).fetchall()
    con.close()
    return [{"pk": r[0], "shortcut": r[1] or "", "phrase": r[2] or ""} for r in rows]

def read_item_by_pk(pk):
    con = get_conn()
    row = con.execute("""
        SELECT Z_PK, ZSHORTCUT, ZPHRASE
        FROM ZTEXTREPLACEMENTENTRY
        WHERE Z_PK = ? AND ZWASDELETED = 0
    """, (pk,)).fetchone()
    con.close()
    if not row:
        return None
    return {"pk": row[0], "shortcut": row[1] or "", "phrase": row[2] or ""}

def insert_item(shortcut, phrase):
    con = get_conn()
    pk  = (con.execute("SELECT MAX(Z_PK) FROM ZTEXTREPLACEMENTENTRY").fetchone()[0] or 0) + 1
    now = _next_timestamp(con)
    con.execute("""
        INSERT INTO ZTEXTREPLACEMENTENTRY
          (Z_PK, Z_ENT, Z_OPT, ZNEEDSSAVETOCLOUD, ZWASDELETED,
           ZTIMESTAMP, ZPHRASE, ZSHORTCUT, ZUNIQUENAME)
        VALUES (?, 1, 4, 1, 0, ?, ?, ?, ?)
    """, (pk, now, phrase, shortcut, str(uuid.uuid4()).upper()))
    con.execute("UPDATE Z_PRIMARYKEY SET Z_MAX=? WHERE Z_ENT=1", (pk,))
    con.commit()
    con.close()
    wal_checkpoint()

def update_item(pk, shortcut, phrase):
    con = get_conn()
    now = _next_timestamp(con)
    con.execute("""
        UPDATE ZTEXTREPLACEMENTENTRY
        SET ZSHORTCUT=?, ZPHRASE=?, ZTIMESTAMP=?, ZNEEDSSAVETOCLOUD=1, Z_OPT=Z_OPT+1
        WHERE Z_PK=?
    """, (shortcut, phrase, now, pk))
    con.commit()
    con.close()
    wal_checkpoint()

def delete_item(pk):
    con = get_conn()
    con.execute("DELETE FROM ZTEXTREPLACEMENTENTRY WHERE Z_PK=?", (pk,))
    con.commit()
    con.close()
    wal_checkpoint()

def stop_keyboard_daemon(ops=None):
    """Sync text replacements to all running apps.
    ops: list of dicts describing the change, e.g.
      {"op": "update", "old_shortcut": ..., "old_phrase": ..., "new_shortcut": ..., "new_phrase": ...}
      {"op": "insert", "shortcut": ..., "phrase": ...}
      {"op": "delete", "shortcut": ..., "phrase": ...}
    When ops is provided, keyboardservicesd is updated directly via XPC without needing
    to read current entries first."""
    items = read_items()
    threading.Thread(target=_sync_to_apps, args=(items, ops), daemon=True).start()

_SYNC_RETRY_DELAYS = [10]

def _sync_to_apps(items, ops=None, _retry=0):
    """Sync text replacements to all apps using the private KeyboardServices XPC API.
    ops: list of operation dicts (from stop_keyboard_daemon). When provided, keyboardservicesd
    is updated directly via modifyEntry/addEntries without reading current state first.
    Steps:
    1. NSUserDefaults update -> updates TextEdit/NSTextView apps immediately
    2. XPC op dispatch -> updates Safari/Slack/Outlook via keyboardservicesd
    3. NSSpellChecker notification -> flushes TextEdit cache
    Retries once after 10s if an XPC op times out (startup race condition)."""
    import json, tempfile

    try:
        payload = {
            "items": [{"replace": i["shortcut"], "with": i["phrase"]} for i in items],
            "ops":   ops or []
        }
        script_path = os.path.join(tempfile.gettempdir(), "txtmanager_ks_sync.py")
        data_path   = os.path.join(tempfile.gettempdir(), "txtmanager_notify.json")

        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(payload, f)

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(r"""
import sys, json, time, os
data_path = sys.argv[1]

with open(data_path, encoding="utf-8") as f:
    data = json.load(f)

import objc
import AppKit
from Foundation import (NSUserDefaults, NSDistributedNotificationCenter,
                        NSRunLoop, NSDate)

AppKit.NSApplication.sharedApplication()

# Register block metadata BEFORE loading the framework.
# textReplacementEntries() always returns empty in subprocess context (no bundle-level
# XPC trust), so we use op-based methods that don't require reading current state.
_void_nsobj_block = {
    'callable': {
        'retval': {'type': b'v'},
        'arguments': {0: {'type': b'@?'}, 1: {'type': b'@'}},
    }
}
_modify_block = {
    'callable': {
        'retval': {'type': b'v'},
        'arguments': {0: {'type': b'@?'}, 1: {'type': b'@'}},
    }
}
objc.registerMetaDataForSelector(
    b'_KSTextReplacementClientStore',
    b'addEntries:removeEntries:withCompletionHandler:',
    {'arguments': {4: _void_nsobj_block}})
objc.registerMetaDataForSelector(
    b'_KSTextReplacementClientStore',
    b'modifyEntry:toEntry:withCompletionHandler:',
    {'arguments': {4: _modify_block}})

objc.loadBundle('KeyboardServices',
    bundle_path='/System/Library/PrivateFrameworks/KeyboardServices.framework',
    module_globals=globals())

KSClientStore = objc.lookUpClass('_KSTextReplacementClientStore')
KSEntry       = objc.lookUpClass('_KSTextReplacementEntry')

# --- Step 1: update NSUserDictionaryReplacementItems plist (for TextEdit) ---
items_list    = data.get("items") or []
entries_plist = [{"on": True, "replace": i["replace"], "with": i["with"]} for i in items_list]
ud = NSUserDefaults.standardUserDefaults()
gd = dict(ud.persistentDomainForName_("NSGlobalDomain") or {})
gd["NSUserDictionaryReplacementItems"] = entries_plist
ud.setPersistentDomain_forName_(gd, "NSGlobalDomain")
ud.synchronize()

# --- Step 2: dispatch individual ops to keyboardservicesd via XPC ---
store    = KSClientStore.alloc().init()
ops      = data.get("ops") or []
timed_out = []

for op in ops:
    done    = [False]
    err_val = [None]

    def _cb(err, _done=done, _err=err_val):
        _err[0]  = err
        _done[0] = True

    op_type = op.get("op")
    if op_type == "update":
        old_e = KSEntry.alloc().init()
        old_e.setShortcut_(op["old_shortcut"])
        old_e.setPhrase_(op["old_phrase"])
        new_e = KSEntry.alloc().init()
        new_e.setShortcut_(op["new_shortcut"])
        new_e.setPhrase_(op["new_phrase"])
        new_e.setNeedsSaveToCloud_(True)
        store.modifyEntry_toEntry_withCompletionHandler_(old_e, new_e, _cb)

    elif op_type == "insert":
        entry = KSEntry.alloc().init()
        entry.setShortcut_(op["shortcut"])
        entry.setPhrase_(op["phrase"])
        entry.setNeedsSaveToCloud_(True)
        store.addEntries_removeEntries_withCompletionHandler_([entry], [], _cb)

    elif op_type == "delete":
        entry = KSEntry.alloc().init()
        entry.setShortcut_(op["shortcut"])
        entry.setPhrase_(op["phrase"])
        store.addEntries_removeEntries_withCompletionHandler_([], [entry], _cb)

    else:
        done[0] = True  # unknown op type, skip

    deadline = time.time() + 5
    while not done[0] and time.time() < deadline:
        NSRunLoop.mainRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.1))

    if not done[0]:
        timed_out.append(op.get("new_shortcut") or op.get("shortcut") or op_type)

if timed_out:
    print(f"XPC timed out for: {timed_out}", file=sys.stderr)
    try: os.unlink(data_path)
    except OSError: pass
    os._exit(1)

if not ops:
    print("XPC step 2 skipped: no ops", file=sys.stderr)

# --- Step 3: notify NSTextView apps (TextEdit) ---
center = NSDistributedNotificationCenter.defaultCenter()
center.postNotificationName_object_userInfo_deliverImmediately_(
    "NSSpellCheckerDidChangeAutomaticTextReplacementNotification", None, None, True)

try: os.unlink(data_path)
except OSError: pass
""")

        clean_env = {k: v for k, v in os.environ.items()
                     if "PYTHON" not in k and k != "RESOURCEPATH"}
        clean_env["PYTHONUTF8"] = "1"

        result = subprocess.run(["/usr/bin/python3", script_path, data_path],
                                timeout=max(15, len(ops or []) * 6),
                                env=clean_env,
                                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if result.returncode != 0:
            stderr_text = result.stderr.decode(errors="replace").strip()
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()} XPC sync script failed "
                        f"(exit {result.returncode}, attempt {_retry + 1}):\n{stderr_text}\n")
            if _retry < len(_SYNC_RETRY_DELAYS):
                delay = _SYNC_RETRY_DELAYS[_retry]
                with open(LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now().isoformat()} Retrying sync in {delay}s "
                            f"(attempt {_retry + 2}/{len(_SYNC_RETRY_DELAYS) + 2})...\n")
                threading.Timer(delay,
                    lambda r=_retry, o=ops: _sync_to_apps(read_items(), o, _retry=r + 1)).start()
            else:
                with open(LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now().isoformat()} All XPC sync attempts failed --"
                            f" DB write is the source of truth, file-watch will propagate.\n")
    except Exception as e:
        import traceback
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} EXCEPTION in _sync_to_apps (attempt {_retry + 1}):\n")
            traceback.print_exc(file=f)
        if _retry < len(_SYNC_RETRY_DELAYS):
            delay = _SYNC_RETRY_DELAYS[_retry]
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()} Retrying sync in {delay}s "
                        f"(attempt {_retry + 2}/{len(_SYNC_RETRY_DELAYS) + 2})...\n")
            threading.Timer(delay,
                lambda r=_retry, o=ops: _sync_to_apps(read_items(), o, _retry=r + 1)).start()
        else:
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()} All sync attempts failed -- giving up.\n")

def find_repeated_tokens(items):
    patterns = [
        r"iPhone[\w\s]+?\(iOS[\s\d.]+\)",
        r"iPad[\w\s]+?\(iPadOS[\s\d.]+\)",
        r"[\w\s]+versjon\s[\d.]+",
        r"\d+\.\d+(?:\.\d+)+",
        r"[A-ZÆØÅ][a-zæøå]+(?:\s[A-ZÆØÅ][a-zæøå]+)+",
        r"\w+",
    ]
    combined = re.compile("|".join(f"(?:{p})" for p in patterns))
    counter  = Counter()
    for item in items:
        for tok in set(combined.findall(item.get("phrase", ""))):
            tok = tok.strip()
            if len(tok) > 2:
                counter[tok] += 1
    return [(tok, cnt) for tok, cnt in counter.most_common() if cnt >= MIN_OCCURRENCES]

# ── Edit dialog ────────────────────────────────────────────────────────────────
class EditDialog(tk.Toplevel):
    def __init__(self, parent, title=None, shortcut="", phrase=""):
        super().__init__(parent)
        self.title(title or t("dlg_new_title"))
        self.resizable(False, False)
        self.configure(bg=COLORS["bg"])
        self.transient(parent)
        self.result = None
        self._build(shortcut, phrase)
        self._center(parent)
        self.grab_set()
        self.wait_window()

    def _center(self, parent):
        self.update_idletasks()
        dw, dh = self.winfo_width(), self.winfo_height()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        self.geometry(f"+{px + (pw - dw) // 2}+{py + (ph - dh) // 2}")

    def _build(self, sc, ph):
        pad = {"padx": 20, "pady": 8}
        tk.Label(self, text=t("dlg_shortcut"), bg=COLORS["bg"], fg=COLORS["text"],
                 font=FONT).grid(row=0, column=0, sticky="w", **pad)
        self.sc_var = tk.StringVar(value=sc)
        sc_frame = tk.Frame(self, bg=COLORS["card"], highlightbackground=COLORS["card_border"],
                            highlightthickness=1, bd=0)
        sc_frame.grid(row=0, column=1, sticky="ew", **pad)
        tk.Entry(sc_frame, textvariable=self.sc_var, width=30,
                 font=FONT, relief="flat", bd=0, bg=COLORS["card"],
                 insertbackground=COLORS["text"]).pack(padx=8, pady=6)

        tk.Label(self, text=t("dlg_phrase"), bg=COLORS["bg"], fg=COLORS["text"],
                 font=FONT).grid(row=1, column=0, sticky="nw", **pad)
        ph_frame = tk.Frame(self, bg=COLORS["card"], highlightbackground=COLORS["card_border"],
                            highlightthickness=1, bd=0)
        ph_frame.grid(row=1, column=1, sticky="ew", **pad)
        self.ph_text = tk.Text(ph_frame, width=52, height=5,
                               font=FONT, wrap="word", relief="flat", bd=0,
                               bg=COLORS["card"], insertbackground=COLORS["text"])
        self.ph_text.insert("1.0", ph)
        self.ph_text.pack(padx=8, pady=6)

        bf = tk.Frame(self, bg=COLORS["bg"])
        bf.grid(row=2, column=0, columnspan=2, pady=16)
        App._make_button(bf, t("dlg_save"),   self._ok,      COLORS["accent"], "white").pack(side="left", padx=6)
        App._make_button(bf, t("dlg_cancel"), self.destroy,  COLORS["secondary"], "white").pack(side="left", padx=6)

    def _ok(self):
        sc = self.sc_var.get().strip()
        ph = self.ph_text.get("1.0", "end-1c").strip()
        if not sc or not ph:
            messagebox.showwarning(t("dlg_missing_title"), t("dlg_missing"), parent=self)
            return
        self.result = (sc, ph)
        self.destroy()

# ── Batch replace dialog ───────────────────────────────────────────────────────
class BatchReplaceDialog(tk.Toplevel):
    def __init__(self, parent, token, count):
        super().__init__(parent)
        self.title(t("batch_title"))
        self.resizable(False, False)
        self.configure(bg=COLORS["bg"])
        self.transient(parent)
        self.result = None
        self._build(token, count)
        self._center(parent)
        self.grab_set()
        self.wait_window()

    def _center(self, parent):
        self.update_idletasks()
        dw, dh = self.winfo_width(), self.winfo_height()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        self.geometry(f"+{px + (pw - dw) // 2}+{py + (ph - dh) // 2}")

    def _build(self, token, count):
        pad = {"padx": 20, "pady": 8}
        tk.Label(self, text=t("batch_replace", n=count), bg=COLORS["bg"], fg=COLORS["text"],
                 font=FONT).grid(row=0, column=0, sticky="w", **pad)
        tk.Label(self, text=token, bg=COLORS["card"], fg=COLORS["text"],
                 font=FONT_BOLD, padx=10, pady=4
                 ).grid(row=0, column=1, sticky="w", **pad)
        tk.Label(self, text=t("batch_with"), bg=COLORS["bg"], fg=COLORS["text"],
                 font=FONT).grid(row=1, column=0, sticky="w", **pad)
        self.new_var = tk.StringVar()
        e_frame = tk.Frame(self, bg=COLORS["card"], highlightbackground=COLORS["card_border"],
                           highlightthickness=1, bd=0)
        e_frame.grid(row=1, column=1, sticky="ew", **pad)
        e = tk.Entry(e_frame, textvariable=self.new_var, width=38, font=FONT,
                     relief="flat", bd=0, bg=COLORS["card"], insertbackground=COLORS["text"])
        e.pack(padx=8, pady=6)
        e.focus_set()
        self.bind("<Return>", lambda _: self._ok())
        bf = tk.Frame(self, bg=COLORS["bg"])
        bf.grid(row=2, column=0, columnspan=2, pady=16)
        App._make_button(bf, t("batch_btn"),  self._ok,     COLORS["accent"], "white").pack(side="left", padx=6)
        App._make_button(bf, t("dlg_cancel"), self.destroy, COLORS["secondary"], "white").pack(side="left", padx=6)

    def _ok(self):
        new = self.new_var.get().strip()
        if not new:
            messagebox.showwarning(t("dlg_missing_val_t"), t("dlg_missing_val"), parent=self)
            return
        self.result = new
        self.destroy()

# ── Modern Apple-style colors ──────────────────────────────────────────────────
COLORS = {
    "bg":           "#f5f5f7",
    "card":         "#ffffff",
    "card_border":  "#d1d1d6",
    "accent":       "#007aff",
    "accent_hover": "#0066d6",
    "destructive":  "#ff3b30",
    "destr_hover":  "#d62d24",
    "secondary":    "#8e8e93",
    "sec_hover":    "#636366",
    "text":         "#1d1d1f",
    "text_sec":     "#86868b",
    "separator":    "#d1d1d6",
    "selected":     "#007aff",
    "status_bg":    "#f2f2f7",
}

FONT       = ("SF Pro Text", 13)
FONT_SMALL = ("SF Pro Text", 11)
FONT_BOLD  = ("SF Pro Text", 13, "bold")
FONT_TITLE = ("SF Pro Display", 20, "bold")

# ── Main window ────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        # Hide window during construction to avoid Cocoa layout crash
        # under py2app's NSTask bootstrap runloop
        self.withdraw()
        self.title(t("title"))
        self.configure(bg=COLORS["bg"])
        self.items = []
        self._build_ui()
        self._build_menu()
        # Defer geometry + show + load until mainloop is running
        self.after(0, self._initialize_window)

    def _build_menu(self):
        menubar = tk.Menu(self)
        tools = tk.Menu(menubar, tearoff=0)
        tools.add_command(label=t("menu_open_log"),   command=self._open_log)
        tools.add_command(label=t("menu_reveal_log"), command=self._reveal_log)
        menubar.add_cascade(label=t("menu_tools"), menu=tools)
        self.config(menu=menubar)

    def _open_log(self):
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        if not os.path.exists(LOG_PATH):
            open(LOG_PATH, "w").close()
        subprocess.run(["open", "-a", "Console", LOG_PATH], capture_output=True)

    def _reveal_log(self):
        if os.path.exists(LOG_PATH):
            subprocess.run(["open", "-R", LOG_PATH], capture_output=True)
        else:
            subprocess.run(["open", os.path.dirname(LOG_PATH)], capture_output=True)

    def _show_update_banner(self, version):
        import webbrowser
        RELEASES_URL = "https://github.com/gesm1s/txtmanager/releases"
        banner = tk.Frame(self, bg="#f6c90e", pady=6)
        banner.pack(fill="x", before=self._title_frame)

        tk.Label(banner, text=f"🆕  {t('update_available', v=version)}",
                 bg="#f6c90e", fg="#333333", font=FONT_SMALL).pack(side="left", padx=16)

        upd = tk.Label(banner, text=t("update_now"),
                       bg="#2e7d32", fg="white", font=FONT_SMALL,
                       cursor="pointinghand", padx=10, pady=4)
        upd.pack(side="left", padx=4)
        upd.bind("<Button-1>", lambda e: self._auto_update(version, banner))

        dl = tk.Label(banner, text=t("update_download"),
                      bg="#d4aa00", fg="#333333", font=FONT_SMALL,
                      cursor="pointinghand", padx=10, pady=4)
        dl.pack(side="left", padx=4)
        dl.bind("<Button-1>", lambda e: webbrowser.open(RELEASES_URL))

        x = tk.Label(banner, text="✕", bg="#f6c90e", fg="#555555",
                     font=FONT_SMALL, cursor="pointinghand", padx=16)
        x.pack(side="right")
        x.bind("<Button-1>", lambda e: banner.destroy())

    def _auto_update(self, version, banner):
        import urllib.request, tempfile

        ZIP_URL = (f"https://github.com/gesm1s/txtmanager/releases"
                   f"/download/v{version}/Txtmanager.zip")

        for w in banner.winfo_children():
            w.destroy()
        progress_lbl = tk.Label(banner, text=t("update_downloading", v=version),
                                bg="#f6c90e", fg="#333333", font=FONT_SMALL)
        progress_lbl.pack(side="left", padx=16, pady=2)

        def _set(msg):
            self.after(0, lambda m=msg: progress_lbl.config(text=m))

        def _do():
            try:
                tmp = tempfile.mkdtemp(prefix="txtmanager_update_")
                zip_path = os.path.join(tmp, "Txtmanager.zip")

                def _hook(count, block, total):
                    if total > 0:
                        pct = min(100, count * block * 100 // total)
                        _set(t("update_downloading", v=version) + f" {pct}%")

                urllib.request.urlretrieve(ZIP_URL, zip_path, _hook)
                _set(t("update_extracting"))

                # ditto -xk preserves Unix permissions (execute bits); zipfile.extractall does not
                extract_dir = os.path.join(tmp, "extracted")
                os.makedirs(extract_dir)
                subprocess.run(["ditto", "-xk", zip_path, extract_dir], check=True)

                new_app = os.path.join(extract_dir, "Txtmanager.app")
                dest = "/Applications/Txtmanager.app"
                _set(t("update_installing"))
                subprocess.run(["rm", "-rf", dest], check=True)
                subprocess.run(["ditto", new_app, dest], check=True)
                subprocess.run(["xattr", "-cr", dest], check=True)

                _set(t("update_restarting"))
                # start_new_session=True calls setsid() so the shell is fully
                # detached and survives os._exit(). -n forces a new instance even
                # if the old bundle ID is still visible to Launch Services.
                subprocess.Popen(
                    ["/bin/sh", "-c", f'sleep 3 && open -n "{dest}"'],
                    start_new_session=True,
                )
                self.after(500, lambda: os._exit(0))

            except Exception as exc:
                _set(t("update_error", e=exc))

        threading.Thread(target=_do, daemon=True).start()

    def _initialize_window(self):
        self.geometry("1100x720")
        self.minsize(900, 500)
        self.resizable(True, True)
        self.deiconify()
        self.after(50, self._load)
        # Check for updates after window is shown — runs in background thread
        _check_for_update(lambda v: self.after(0, lambda: self._show_update_banner(v)))

    @staticmethod
    def _center_dialog(dialog, parent):
        """Center a Toplevel dialog over its parent window."""
        dialog.update_idletasks()
        dw, dh = dialog.winfo_width(), dialog.winfo_height()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        x = px + (pw - dw) // 2
        y = py + (ph - dh) // 2
        dialog.geometry(f"+{x}+{y}")

    @staticmethod
    def _make_button(container, text, command, bg, fg, width=None):
        """Create a modern rounded button using a Frame+Label approach."""
        btn_frame = tk.Frame(container, bg=bg, padx=14, pady=6, cursor="pointinghand",
                             highlightthickness=0, bd=0)
        lbl = tk.Label(btn_frame, text=text, bg=bg, fg=fg, font=FONT_SMALL,
                       cursor="pointinghand")
        lbl.pack()

        hover_bg = _darken(bg)
        def on_enter(e):
            btn_frame.config(bg=hover_bg)
            lbl.config(bg=hover_bg)
        def on_leave(e):
            btn_frame.config(bg=bg)
            lbl.config(bg=bg)
        def on_click(e):
            command()

        for widget in (btn_frame, lbl):
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)

        if width:
            btn_frame.config(width=width)
        return btn_frame

    def _build_ui(self):
        style = ttk.Style(self)
        style.theme_use("aqua" if "aqua" in style.theme_names() else "clam")

        # Treeview styling
        style.configure("Treeview",
            background="white", foreground=COLORS["text"],
            fieldbackground="white", rowheight=32, font=FONT,
            borderwidth=0, relief="flat")
        style.configure("Treeview.Heading",
            background=COLORS["bg"], foreground=COLORS["text"],
            font=FONT_BOLD, relief="flat", borderwidth=0)
        style.map("Treeview",
            background=[("selected", COLORS["selected"])],
            foreground=[("selected", "white")])
        style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

        # Title
        title_frame = tk.Frame(self, bg=COLORS["bg"])
        self._title_frame = title_frame
        title_frame.pack(fill="x", padx=24, pady=(20, 4))
        tk.Label(title_frame, text=t("title"), bg=COLORS["bg"], fg=COLORS["text"],
                 font=FONT_TITLE).pack(side="left")
        tk.Label(title_frame, text=t("version_label", v=APP_VERSION, b=APP_BUILD),
                 bg=COLORS["bg"], fg=COLORS["text_sec"], font=FONT_SMALL).pack(side="right", pady=8)

        # Main content area
        main = tk.Frame(self, bg=COLORS["bg"])
        main.pack(fill="both", expand=True, padx=24, pady=(8, 16))

        # ── Left panel ──
        left = tk.Frame(main, bg=COLORS["bg"])
        left.pack(side="left", fill="both", expand=True)

        # Search bar — modern rounded style
        sf = tk.Frame(left, bg=COLORS["card"], highlightbackground=COLORS["card_border"],
                      highlightthickness=1, bd=0)
        sf.pack(fill="x", pady=(0, 12))
        tk.Label(sf, text="🔍", bg=COLORS["card"], font=FONT).pack(side="left", padx=(12, 4), pady=8)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh_table())
        search_entry = tk.Entry(sf, textvariable=self.search_var, width=38,
                 font=FONT, relief="flat", bd=0, bg=COLORS["card"],
                 insertbackground=COLORS["text"])
        search_entry.pack(side="left", fill="x", expand=True, padx=4, pady=8)
        clear_btn = tk.Label(sf, text="✕", bg=COLORS["card"], fg=COLORS["text_sec"],
                             font=FONT_SMALL, cursor="pointinghand")
        clear_btn.pack(side="right", padx=(4, 12), pady=8)
        clear_btn.bind("<Button-1>", lambda e: self.search_var.set(""))

        # Treeview in a card-like container
        tcard = tk.Frame(left, bg=COLORS["card"], highlightbackground=COLORS["card_border"],
                         highlightthickness=1, bd=0)
        tcard.pack(fill="both", expand=True)
        tframe = tk.Frame(tcard, bg=COLORS["card"])
        tframe.pack(fill="both", expand=True, padx=1, pady=1)
        self.tree = ttk.Treeview(tframe, columns=("shortcut", "phrase"),
                                  show="headings", selectmode="browse")
        self.tree.heading("shortcut", text=t("col_shortcut"), command=lambda: self._sort("shortcut"))
        self.tree.heading("phrase",   text=t("col_phrase"),   command=lambda: self._sort("phrase"))
        self.tree.column("shortcut", width=180, minwidth=80, stretch=False)
        self.tree.column("phrase",   width=500, minwidth=200, stretch=True)
        sb = ttk.Scrollbar(tframe, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", lambda e: self._edit_selected())

        # Button bar
        bf = tk.Frame(left, bg=COLORS["bg"], pady=12)
        bf.pack(fill="x")
        for label, cmd, bg_c, fg_c in [
            (t("btn_new"),          self._add,             COLORS["accent"],      "white"),
            (t("btn_edit"),         self._edit_selected,   COLORS["accent"],      "white"),
            (t("btn_delete"),       self._delete_selected, COLORS["destructive"], "white"),
            (t("btn_findreplace"),  self._find_replace,    COLORS["secondary"],   "white"),
            (t("btn_version_bump"), self._version_bump,    COLORS["secondary"],   "white"),
        ]:
            self._make_button(bf, label, cmd, bg_c, fg_c).pack(side="left", padx=(0, 8))
        self._make_button(bf, t("btn_reload"), self._load, COLORS["secondary"], "white").pack(side="right")

        # ── Right panel (repeated tokens) ──
        right = tk.Frame(main, bg=COLORS["bg"], width=240)
        right.pack(side="right", fill="y", padx=(20, 0))
        right.pack_propagate(False)

        tk.Label(right, text=t("repeated_title"), bg=COLORS["bg"], fg=COLORS["text"],
                 font=FONT_BOLD).pack(anchor="w", pady=(0, 4))
        tk.Label(right, text=t("repeated_hint"), bg=COLORS["bg"], fg=COLORS["text_sec"],
                 font=FONT_SMALL, wraplength=220).pack(anchor="w", pady=(0, 12))

        lf_card = tk.Frame(right, bg=COLORS["card"], highlightbackground=COLORS["card_border"],
                           highlightthickness=1, bd=0)
        lf_card.pack(fill="both", expand=True)
        lf = tk.Frame(lf_card, bg=COLORS["card"])
        lf.pack(fill="both", expand=True, padx=1, pady=1)
        self.token_list = tk.Listbox(lf, font=FONT, relief="flat", bd=0,
                                     bg=COLORS["card"],
                                     selectbackground=COLORS["selected"], selectforeground="white",
                                     activestyle="none", highlightthickness=0)
        tsb = ttk.Scrollbar(lf, orient="vertical", command=self.token_list.yview)
        self.token_list.configure(yscrollcommand=tsb.set)
        self.token_list.pack(side="left", fill="both", expand=True)
        tsb.pack(side="right", fill="y")
        self.token_list.bind("<<ListboxSelect>>", self._on_token_select)

        self.selected_token_var = tk.StringVar(value=t("repeated_none"))
        tk.Label(right, text=t("repeated_selected"), bg=COLORS["bg"], fg=COLORS["text_sec"],
                 font=FONT_SMALL).pack(anchor="w", pady=(12, 2))
        tk.Label(right, textvariable=self.selected_token_var, bg=COLORS["bg"], fg=COLORS["text"],
                 font=FONT_BOLD, wraplength=220, justify="left").pack(anchor="w")

        tk.Label(right, text=t("repeated_new_value"), bg=COLORS["bg"], fg=COLORS["text_sec"],
                 font=FONT_SMALL).pack(anchor="w", pady=(12, 2))
        self.token_new_var = tk.StringVar()
        token_entry_frame = tk.Frame(right, bg=COLORS["card"], highlightbackground=COLORS["card_border"],
                                     highlightthickness=1, bd=0)
        token_entry_frame.pack(fill="x")
        token_entry = tk.Entry(token_entry_frame, textvariable=self.token_new_var,
                       font=FONT, relief="flat", bd=0, bg=COLORS["card"],
                       insertbackground=COLORS["text"])
        token_entry.pack(fill="x", padx=8, pady=6)
        token_entry.bind("<Return>", lambda _: self._apply_selected_token_replace())

        self._make_button(right, t("repeated_apply"), self._apply_selected_token_replace,
                  COLORS["accent"], "white").pack(fill="x", pady=(12, 0))
        self._make_button(right, t("btn_update_list"), self._refresh_tokens,
                  COLORS["secondary"], "white").pack(fill="x", pady=(8, 0))

        # Status bar
        self.status_var = tk.StringVar(value="")
        status_frame = tk.Frame(self, bg=COLORS["status_bg"])
        status_frame.pack(fill="x", side="bottom")
        tk.Label(status_frame, textvariable=self.status_var, bg=COLORS["status_bg"],
                 fg=COLORS["text_sec"], font=FONT_SMALL, anchor="w", padx=24
                 ).pack(fill="x", ipady=6)

    def _sort(self, col):
        if not hasattr(self, "_sort_state"):
            self._sort_state = {}
        rev = self._sort_state.get(col, False)
        self.items.sort(key=lambda x: x.get(col, "").lower(), reverse=rev)
        self._sort_state[col] = not rev
        self._refresh_table()

    def _load(self):
        try:
            self.items = read_items()
            self._refresh_table()
            self._refresh_tokens()
            self._status(t("status_loaded", n=len(self.items)))
        except Exception as e:
            messagebox.showerror("Error", t("err_db", e=e))

    def _refresh_table(self):
        q = self.search_var.get().lower()
        self.tree.delete(*self.tree.get_children())
        for item in self.items:
            sc = item.get("shortcut", "")
            ph = item.get("phrase", "")
            if q and q not in sc.lower() and q not in ph.lower():
                continue
            self.tree.insert("", "end", iid=str(item["pk"]), values=(sc, ph))

    def _refresh_tokens(self):
        self.token_list.delete(0, "end")
        self._tokens = find_repeated_tokens(self.items)
        for tok, cnt in self._tokens:
            self.token_list.insert("end", f"{tok}  ({cnt})")
        self.selected_token_var.set(t("repeated_none"))
        self.token_new_var.set("")

    def _status(self, msg):
        self.status_var.set(msg)

    def _verify_saved_rows(self, expected_rows, retries=3, delay=0.3):
        """Non-blocking verification in background thread."""
        def _check():
            for _ in range(retries):
                time.sleep(delay)
                all_ok = True
                for exp in expected_rows:
                    current = read_item_by_pk(exp["pk"])
                    if not current:
                        all_ok = False
                        break
                    if current["shortcut"] != exp["shortcut"] or current["phrase"] != exp["phrase"]:
                        all_ok = False
                        break
                if all_ok:
                    return
            self.after(0, lambda: messagebox.showwarning(t("warn_sync_title"), t("warn_sync_msg")))
        threading.Thread(target=_check, daemon=True).start()

    def _selected_item(self):
        sel = self.tree.selection()
        if not sel:
            return None
        pk = int(sel[0])
        return next((i for i in self.items if i["pk"] == pk), None)

    def _on_token_select(self, event=None):
        idx = self.token_list.curselection()
        if not idx:
            return
        token, _count = self._tokens[idx[0]]
        self.selected_token_var.set(token)
        self.token_new_var.set(token)

    def _apply_selected_token_replace(self):
        idx = self.token_list.curselection()
        if not idx:
            messagebox.showinfo(t("select_expression_t"), t("select_expression"))
            return

        token, _count = self._tokens[idx[0]]
        new_val = self.token_new_var.get().strip()
        if not new_val:
            messagebox.showwarning(t("dlg_missing_val_t"), t("dlg_missing_val"))
            return
        if new_val == token:
            return

        affected = [i for i in self.items if token in i.get("phrase", "")]
        ops = [{"op": "update",
                "old_shortcut": i["shortcut"], "old_phrase": i["phrase"],
                "new_shortcut": i["shortcut"], "new_phrase": i["phrase"].replace(token, new_val)}
               for i in affected]
        backup()
        expected = []
        for item in affected:
            new_phrase = item["phrase"].replace(token, new_val)
            update_item(item["pk"], item["shortcut"], new_phrase)
            item["phrase"] = new_phrase
            expected.append({"pk": item["pk"], "shortcut": item["shortcut"], "phrase": new_phrase})
        stop_keyboard_daemon(ops=ops)
        self._verify_saved_rows(expected)
        self._refresh_table()
        self._refresh_tokens()
        self._status(t("status_replaced", a=token, b=new_val, n=len(affected)))

    def _add(self):
        dlg = EditDialog(self, title=t("dlg_new_title"))
        if not dlg.result:
            return
        sc, ph = dlg.result
        if any(_normalize_shortcut(i["shortcut"]) == _normalize_shortcut(sc) for i in self.items):
            messagebox.showerror(t("err_exists_title"), t("err_exists", s=sc))
            return
        backup()
        insert_item(sc, ph)
        stop_keyboard_daemon(ops=[{"op": "insert", "shortcut": sc, "phrase": ph}])
        self._load()
        self._status(t("status_added", s=sc))

    def _edit_selected(self):
        item = self._selected_item()
        if not item:
            messagebox.showinfo(t("select_row_title"), t("select_row"))
            return
        dlg = EditDialog(self, title=t("dlg_edit_title"),
                         shortcut=item["shortcut"], phrase=item["phrase"])
        if not dlg.result:
            return
        new_shortcut = dlg.result[0]
        if any(
            i["pk"] != item["pk"] and
            _normalize_shortcut(i["shortcut"]) == _normalize_shortcut(new_shortcut)
            for i in self.items
        ):
            messagebox.showerror(t("err_exists_title"), t("err_exists", s=new_shortcut))
            return
        backup()
        update_item(item["pk"], new_shortcut, dlg.result[1])
        stop_keyboard_daemon(ops=[{
            "op": "update",
            "old_shortcut": item["shortcut"], "old_phrase": item["phrase"],
            "new_shortcut": new_shortcut,     "new_phrase": dlg.result[1]
        }])
        self._verify_saved_rows([
            {"pk": item["pk"], "shortcut": new_shortcut, "phrase": dlg.result[1]}
        ])
        self._load()
        self._status(t("status_edited", s=item["shortcut"]))

    def _delete_selected(self):
        item = self._selected_item()
        if not item:
            messagebox.showinfo(t("select_row_title"), t("select_row"))
            return
        if not messagebox.askyesno(t("confirm_title"), t("confirm_delete", s=item["shortcut"])):
            return
        backup()
        delete_item(item["pk"])
        stop_keyboard_daemon(ops=[{"op": "delete", "shortcut": item["shortcut"], "phrase": item["phrase"]}])
        self._load()
        self._status(t("status_deleted", s=item["shortcut"]))

    def _version_bump(self):
        """Detect version numbers in phrases and offer a quick bump UI."""
        version_re = re.compile(r"\d+\.\d+(?:\.\d+)*")
        version_counts = Counter()
        for item in self.items:
            for m in version_re.finditer(item.get("phrase", "")):
                version_counts[m.group()] += 1
        # Only show versions appearing in 2+ phrases
        versions = [(v, c) for v, c in version_counts.most_common() if c >= 2]
        if not versions:
            messagebox.showinfo(t("vb_no_versions_t"), t("vb_no_versions"))
            return

        win = tk.Toplevel(self)
        win.title(t("vb_title"))
        win.configure(bg=COLORS["bg"])
        win.resizable(False, False)
        win.transient(self)

        tk.Label(win, text=t("vb_title"), bg=COLORS["bg"], fg=COLORS["text"],
                 font=FONT_BOLD).pack(anchor="w", padx=20, pady=(16, 8))

        # Version list
        list_frame = tk.Frame(win, bg=COLORS["card"], highlightbackground=COLORS["card_border"],
                              highlightthickness=1, bd=0)
        list_frame.pack(fill="both", padx=20, pady=(0, 8))
        ver_list = tk.Listbox(list_frame, font=FONT, relief="flat", bd=0, bg=COLORS["card"],
                              selectbackground=COLORS["selected"], selectforeground="white",
                              activestyle="none", highlightthickness=0, height=min(8, len(versions)))
        ver_list.pack(fill="both", padx=1, pady=1)
        for v, c in versions:
            ver_list.insert("end", f"{v}  ({c} snarveier)" if LANG == "no" else f"{v}  ({c} shortcuts)")

        # New version entry
        entry_frame = tk.Frame(win, bg=COLORS["bg"])
        entry_frame.pack(fill="x", padx=20, pady=(4, 8))
        tk.Label(entry_frame, text=t("vb_new"), bg=COLORS["bg"], fg=COLORS["text"],
                 font=FONT).pack(side="left")
        new_ver_var = tk.StringVar()
        nv_frame = tk.Frame(entry_frame, bg=COLORS["card"], highlightbackground=COLORS["card_border"],
                            highlightthickness=1, bd=0)
        nv_frame.pack(side="left", padx=(8, 0), fill="x", expand=True)
        new_entry = tk.Entry(nv_frame, textvariable=new_ver_var, font=FONT,
                             relief="flat", bd=0, bg=COLORS["card"],
                             insertbackground=COLORS["text"])
        new_entry.pack(padx=8, pady=6, fill="x")

        # Preview of affected shortcuts
        preview_var = tk.StringVar(value="")
        tk.Label(win, textvariable=preview_var, bg=COLORS["bg"], fg=COLORS["text_sec"],
                 font=FONT_SMALL, wraplength=400, justify="left").pack(anchor="w", padx=20, pady=(0, 4))

        def on_select(event=None):
            idx = ver_list.curselection()
            if not idx:
                return
            ver, cnt = versions[idx[0]]
            new_ver_var.set(ver)
            affected = [i["shortcut"] for i in self.items if ver in i.get("phrase", "")]
            preview_var.set(t("vb_affected", n=cnt) + " " + ", ".join(affected[:10])
                           + ("…" if len(affected) > 10 else ""))

        ver_list.bind("<<ListboxSelect>>", on_select)

        def do_bump():
            idx = ver_list.curselection()
            if not idx:
                return
            old_ver = versions[idx[0]][0]
            new_ver = new_ver_var.get().strip()
            if not new_ver or new_ver == old_ver:
                return
            affected = [i for i in self.items if old_ver in i.get("phrase", "")]
            ops = [{"op": "update",
                    "old_shortcut": i["shortcut"], "old_phrase": i["phrase"],
                    "new_shortcut": i["shortcut"], "new_phrase": i["phrase"].replace(old_ver, new_ver)}
                   for i in affected]
            backup()
            expected = []
            for item in affected:
                new_phrase = item["phrase"].replace(old_ver, new_ver)
                update_item(item["pk"], item["shortcut"], new_phrase)
                item["phrase"] = new_phrase
                expected.append({"pk": item["pk"], "shortcut": item["shortcut"], "phrase": new_phrase})
            stop_keyboard_daemon(ops=ops)
            self._verify_saved_rows(expected)
            self._refresh_table()
            self._refresh_tokens()
            self._status(t("vb_done", a=old_ver, b=new_ver, n=len(affected)))
            win.destroy()

        new_entry.bind("<Return>", lambda _: do_bump())

        bf = tk.Frame(win, bg=COLORS["bg"])
        bf.pack(pady=(4, 16))
        self._make_button(bf, t("vb_apply"), do_bump, COLORS["accent"], "white").pack(side="left", padx=6)
        self._make_button(bf, t("dlg_cancel"), win.destroy, COLORS["secondary"], "white").pack(side="left", padx=6)

        self._center_dialog(win, self)

    def _find_replace(self):
        win = tk.Toplevel(self)
        win.title(t("find_title"))
        win.configure(bg=COLORS["bg"])
        win.resizable(False, False)
        win.transient(self)
        pad = {"padx": 20, "pady": 8}
        for row, lbl in enumerate([t("find_label"), t("replace_label")]):
            tk.Label(win, text=lbl, bg=COLORS["bg"], fg=COLORS["text"],
                     font=FONT).grid(row=row, column=0, sticky="w", **pad)
        fv, rv = tk.StringVar(), tk.StringVar()
        for row, var in enumerate([fv, rv]):
            e_frame = tk.Frame(win, bg=COLORS["card"], highlightbackground=COLORS["card_border"],
                               highlightthickness=1, bd=0)
            e_frame.grid(row=row, column=1, sticky="ew", **pad)
            tk.Entry(e_frame, textvariable=var, width=40,
                     font=FONT, relief="flat", bd=0, bg=COLORS["card"],
                     insertbackground=COLORS["text"]).pack(padx=8, pady=6)

        original_query = self.search_var.get()
        matches_var = tk.StringVar(value=t("find_matches", n=0))
        tk.Label(win, textvariable=matches_var, bg=COLORS["bg"], fg=COLORS["text_sec"],
                 font=FONT_SMALL).grid(row=2, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 6))

        def update_preview(*_):
            f = fv.get()
            if f:
                self.search_var.set(f)
                f_lower = f.lower()
                n = sum(1 for i in self.items if f_lower in i.get("phrase", "").lower())
            else:
                self.search_var.set(original_query)
                n = 0
            matches_var.set(t("find_matches", n=n))

        fv.trace_add("write", update_preview)

        def do_replace():
            f, r = fv.get(), rv.get()
            if not f:
                return
            affected = [i for i in self.items if f in i.get("phrase", "")]
            if not affected:
                messagebox.showinfo(t("err_no_match_title"), t("err_no_match", f=f))
                return
            ops = [{"op": "update",
                    "old_shortcut": item["shortcut"], "old_phrase": item["phrase"],
                    "new_shortcut": item["shortcut"], "new_phrase": item["phrase"].replace(f, r)}
                   for item in affected]
            backup()
            expected = []
            for item in affected:
                new_phrase = item["phrase"].replace(f, r)
                update_item(item["pk"], item["shortcut"], new_phrase)
                expected.append({"pk": item["pk"], "shortcut": item["shortcut"], "phrase": new_phrase})
            stop_keyboard_daemon(ops=ops)
            self._verify_saved_rows(expected)
            self._load()
            self._status(t("status_findreplace", n=len(affected)))
            self.search_var.set(original_query)
            win.destroy()

        def close_dialog():
            self.search_var.set(original_query)
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", close_dialog)

        bf = tk.Frame(win, bg=COLORS["bg"])
        bf.grid(row=3, column=0, columnspan=2, pady=16)
        self._make_button(bf, t("find_btn"),    do_replace,  COLORS["accent"], "white").pack(side="left", padx=6)
        self._make_button(bf, t("dlg_cancel"),  close_dialog, COLORS["secondary"], "white").pack(side="left", padx=6)

        self._center_dialog(win, self)

# ── Start ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    App().mainloop()