#!/usr/bin/env python3
"""
Teksterstatning Manager for macOS 15+/26
- Leser og skriver direkte til ~/Library/KeyboardServices/TextReplacements.db
- Ingen eksport/import nødvendig
- Synkroniserer automatisk til iPhone/iPad via CloudKit
"""

import sqlite3, time, uuid, subprocess, os, re, shutil
from collections import Counter
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

def _darken(hex_color):
    """Gjør en farge litt mørkere for hover-effekt."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    r, g, b = max(0,r-30), max(0,g-30), max(0,b-30)
    return f"#{r:02x}{g:02x}{b:02x}"

# ── Konfigurasjon ──────────────────────────────────────────────────────────────
DB_PATH  = os.path.expanduser("~/Library/KeyboardServices/TextReplacements.db")
CD_EPOCH = 978307200  # sekunder mellom Unix epoch og CoreData epoch (2001-01-01)
MIN_OCCURRENCES = 2

# ── Backend ────────────────────────────────────────────────────────────────────
def backup():
    ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = DB_PATH + f".backup_{ts}"
    shutil.copy2(DB_PATH, dst)

def get_conn():
    return sqlite3.connect(DB_PATH)

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

def next_pk(con):
    pk = con.execute("SELECT MAX(Z_PK) FROM ZTEXTREPLACEMENTENTRY").fetchone()[0]
    return (pk or 0) + 1

def insert_item(shortcut, phrase):
    con = get_conn()
    pk  = next_pk(con)
    now = time.time() - CD_EPOCH
    con.execute("""
        INSERT INTO ZTEXTREPLACEMENTENTRY
          (Z_PK, Z_ENT, Z_OPT, ZNEEDSSAVETOCLOUD, ZWASDELETED,
           ZTIMESTAMP, ZPHRASE, ZSHORTCUT, ZUNIQUENAME)
        VALUES (?, 1, 4, 1, 0, ?, ?, ?, ?)
    """, (pk, now, phrase, shortcut, str(uuid.uuid4()).upper()))
    con.execute("UPDATE Z_PRIMARYKEY SET Z_MAX=? WHERE Z_ENT=1", (pk,))
    con.commit()
    con.close()

def update_item(pk, shortcut, phrase):
    now = time.time() - CD_EPOCH
    con = get_conn()
    con.execute("""
        UPDATE ZTEXTREPLACEMENTENTRY
        SET ZSHORTCUT=?, ZPHRASE=?, ZTIMESTAMP=?, ZNEEDSSAVETOCLOUD=1
        WHERE Z_PK=?
    """, (shortcut, phrase, now, pk))
    con.commit()
    con.close()

def delete_item(pk):
    con = get_conn()
    con.execute("DELETE FROM ZTEXTREPLACEMENTENTRY WHERE Z_PK=?", (pk,))
    con.commit()
    con.close()

def restart_keyboard_daemon():
    try:
        pid = subprocess.check_output(["pgrep", "keyboardservicesd"]).decode().strip()
        subprocess.run(["kill", pid])
    except Exception:
        pass  # Daemonen starter selv opp igjen

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
        tokens = set(combined.findall(item.get("phrase", "")))
        for t in tokens:
            t = t.strip()
            if len(t) > 2:
                counter[t] += 1
    return [(tok, cnt) for tok, cnt in counter.most_common()
            if cnt >= MIN_OCCURRENCES]

# ── Dialogboks: rediger én snarvei ────────────────────────────────────────────
class EditDialog(tk.Toplevel):
    def __init__(self, parent, title="Snarvei", shortcut="", phrase=""):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.configure(bg="white")
        self.result = None
        self._build(shortcut, phrase)
        self.grab_set()
        self.wait_window()

    def _build(self, sc, ph):
        pad = {"padx": 16, "pady": 6}
        tk.Label(self, text="Snarvei:", bg="white",
                 font=("SF Pro Text", 12)).grid(row=0, column=0, sticky="w", **pad)
        self.sc_var = tk.StringVar(value=sc)
        tk.Entry(self, textvariable=self.sc_var, width=30,
                 font=("SF Pro Text", 12)).grid(row=0, column=1, sticky="ew", **pad)

        tk.Label(self, text="Frase:", bg="white",
                 font=("SF Pro Text", 12)).grid(row=1, column=0, sticky="nw", **pad)
        self.ph_text = tk.Text(self, width=52, height=5,
                               font=("SF Pro Text", 12), wrap="word",
                               relief="solid", bd=1)
        self.ph_text.insert("1.0", ph)
        self.ph_text.grid(row=1, column=1, sticky="ew", **pad)

        bf = tk.Frame(self, bg="white")
        bf.grid(row=2, column=0, columnspan=2, pady=10)
        tk.Button(bf, text="Lagre", command=self._ok,
                  bg="#34c759", fg="white", relief="flat",
                  font=("SF Pro Text", 12, "bold"), padx=14).pack(side="left", padx=6)
        tk.Button(bf, text="Avbryt", command=self.destroy,
                  relief="flat", font=("SF Pro Text", 12), padx=14).pack(side="left", padx=6)

    def _ok(self):
        sc = self.sc_var.get().strip()
        ph = self.ph_text.get("1.0", "end-1c").strip()
        if not sc or not ph:
            messagebox.showwarning("Mangler data", "Fyll ut begge felt.", parent=self)
            return
        self.result = (sc, ph)
        self.destroy()

# ── Dialogboks: batch-erstatt ─────────────────────────────────────────────────
class BatchReplaceDialog(tk.Toplevel):
    def __init__(self, parent, token, count):
        super().__init__(parent)
        self.title("Oppdater alle forekomster")
        self.resizable(False, False)
        self.configure(bg="white")
        self.result = None
        self._build(token, count)
        self.grab_set()
        self.wait_window()

    def _build(self, token, count):
        pad = {"padx": 16, "pady": 8}
        tk.Label(self, text=f"Erstatt ({count} fraser):", bg="white",
                 font=("SF Pro Text", 12)).grid(row=0, column=0, sticky="w", **pad)
        tk.Label(self, text=token, bg="#f0f0f0",
                 font=("SF Pro Text", 12, "bold"), padx=8, pady=4
                 ).grid(row=0, column=1, sticky="w", **pad)

        tk.Label(self, text="Med:", bg="white",
                 font=("SF Pro Text", 12)).grid(row=1, column=0, sticky="w", **pad)
        self.new_var = tk.StringVar()
        e = tk.Entry(self, textvariable=self.new_var, width=38,
                     font=("SF Pro Text", 12))
        e.grid(row=1, column=1, sticky="ew", **pad)
        e.focus_set()
        self.bind("<Return>", lambda _: self._ok())

        bf = tk.Frame(self, bg="white")
        bf.grid(row=2, column=0, columnspan=2, pady=10)
        tk.Button(bf, text="Erstatt i alle fraser", command=self._ok,
                  bg="#007aff", fg="white", relief="flat",
                  font=("SF Pro Text", 12, "bold"), padx=14).pack(side="left", padx=6)
        tk.Button(bf, text="Avbryt", command=self.destroy,
                  relief="flat", font=("SF Pro Text", 12), padx=14).pack(side="left", padx=6)

    def _ok(self):
        new = self.new_var.get().strip()
        if not new:
            messagebox.showwarning("Mangler verdi", "Skriv inn ny verdi.", parent=self)
            return
        self.result = new
        self.destroy()

# ── Hovedvindu ─────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Teksterstatning Manager")
        self.geometry("1050x660")
        self.resizable(True, True)
        self.configure(bg="#f5f5f7")
        self.items = []
        self._build_ui()
        self._load()

    def _make_button(self, parent, text, command, bg, fg):
        c = tk.Canvas(parent, bg=bg, highlightthickness=0,
                      cursor="hand2", height=32)
        c.pack_configure()
        def _draw(event=None):
            c.delete("all")
            w, h = c.winfo_width() or 120, c.winfo_height() or 32
            c.config(width=w)
            c.create_rectangle(0, 0, w, h, fill=bg, outline="")
            c.create_text(w//2, h//2, text=text, fill=fg,
                          font=("SF Pro Text", 12))
        c.bind("<Configure>", _draw)
        c.bind("<Button-1>", lambda e: command())
        c.bind("<Enter>",  lambda e: c.config(bg=_darken(bg)))
        c.bind("<Leave>",  lambda e: c.config(bg=bg))
        # Estimer bredde basert på tekstlengde
        c.config(width=len(text) * 9 + 24, height=32)
        return c

    def _build_ui(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview",
            background="white", foreground="#1d1d1f",
            fieldbackground="white", rowheight=26,
            font=("SF Pro Text", 13))
        style.configure("Treeview.Heading",
            background="#e5e5ea", foreground="#1d1d1f",
            font=("SF Pro Text", 12, "bold"))
        style.map("Treeview",
            background=[("selected", "#0071e3")],
            foreground=[("selected", "white")])

        tk.Label(self, text="🔤 Teksterstatning Manager",
                 bg="#f5f5f7", fg="#1d1d1f",
                 font=("SF Pro Text", 17, "bold")
                 ).pack(anchor="w", padx=16, pady=(14, 6))

        main = tk.Frame(self, bg="#f5f5f7")
        main.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        # ── VENSTRE ──
        left = tk.Frame(main, bg="#f5f5f7")
        left.pack(side="left", fill="both", expand=True)

        sf = tk.Frame(left, bg="#f5f5f7")
        sf.pack(fill="x", pady=(0, 6))
        tk.Label(sf, text="🔍", bg="#f5f5f7",
                 font=("SF Pro Text", 14)).pack(side="left", padx=(0, 4))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh_table())
        tk.Entry(sf, textvariable=self.search_var, width=38,
                 font=("SF Pro Text", 13), relief="solid", bd=1
                 ).pack(side="left")
        tk.Button(sf, text="✕", command=lambda: self.search_var.set(""),
                  bg="#f5f5f7", relief="flat",
                  font=("SF Pro Text", 12)).pack(side="left", padx=4)

        tframe = tk.Frame(left, bg="#f5f5f7")
        tframe.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(tframe, columns=("shortcut", "phrase"),
                                  show="headings", selectmode="browse")
        self.tree.heading("shortcut", text="Snarvei",
                          command=lambda: self._sort("shortcut"))
        self.tree.heading("phrase",   text="Frase",
                          command=lambda: self._sort("phrase"))
        self.tree.column("shortcut", width=170, minwidth=80, stretch=False)
        self.tree.column("phrase",   width=500, minwidth=200, stretch=True)
        sb = ttk.Scrollbar(tframe, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", lambda e: self._edit_selected())

        bf = tk.Frame(left, bg="#f5f5f7", pady=8)
        bf.pack(fill="x")
        btn_configs = [
            ("➕ Ny",          self._add,             "#0051a8", "white"),
            ("✏️  Endre",       self._edit_selected,   "#0051a8", "white"),
            ("🗑  Slett",       self._delete_selected, "#c0001e", "white"),
            ("🔄 Finn/Erstatt", self._find_replace,    "#3a3a3a", "white"),
        ]
        for label, cmd, bg, fg in btn_configs:
            self._make_button(bf, label, cmd, bg, fg).pack(side="left", padx=(0, 8))
        self._make_button(bf, "↺ Last inn på nytt", self._load,
                          "#888888", "white").pack(side="right")

        # ── HØYRE: gjentakende verdier ──
        right = tk.Frame(main, bg="#f5f5f7", width=220)
        right.pack(side="right", fill="y", padx=(14, 0))
        right.pack_propagate(False)

        tk.Label(right, text="Gjentakende verdier",
                 bg="#f5f5f7", fg="#1d1d1f",
                 font=("SF Pro Text", 12, "bold")).pack(anchor="w", pady=(0, 2))
        tk.Label(right, text="Dobbeltklikk for å erstatte i alle fraser",
                 bg="#f5f5f7", fg="#636366",
                 font=("SF Pro Text", 10), wraplength=200
                 ).pack(anchor="w", pady=(0, 8))

        lf = tk.Frame(right, bg="#f5f5f7")
        lf.pack(fill="both", expand=True)
        self.token_list = tk.Listbox(lf, font=("SF Pro Text", 12),
                                     relief="solid", bd=1,
                                     selectbackground="#0071e3",
                                     selectforeground="white",
                                     activestyle="none")
        tsb = ttk.Scrollbar(lf, orient="vertical", command=self.token_list.yview)
        self.token_list.configure(yscrollcommand=tsb.set)
        self.token_list.pack(side="left", fill="both", expand=True)
        tsb.pack(side="right", fill="y")
        self.token_list.bind("<Double-1>", self._on_token_click)

        tk.Button(right, text="↺ Oppdater liste", command=self._refresh_tokens,
                  bg="#e5e5ea", fg="#1d1d1f", relief="flat",
                  font=("SF Pro Text", 11), pady=4
                  ).pack(fill="x", pady=(8, 0))

        self.status_var = tk.StringVar(value="Klar.")
        tk.Label(self, textvariable=self.status_var,
                 bg="#e5e5ea", fg="#636366",
                 font=("SF Pro Text", 11), anchor="w", padx=12
                 ).pack(fill="x", side="bottom", ipady=4)

    # ── Sortering ──────────────────────────────────────────────────────────────
    def _sort(self, col):
        if not hasattr(self, "_sort_state"):
            self._sort_state = {}
        rev = self._sort_state.get(col, False)
        self.items.sort(key=lambda x: x.get(col, "").lower(), reverse=rev)
        self._sort_state[col] = not rev
        self._refresh_table()

    # ── Data ───────────────────────────────────────────────────────────────────
    def _load(self):
        try:
            self.items = read_items()
            self._refresh_table()
            self._refresh_tokens()
            self._status(f"Lastet {len(self.items)} snarveier direkte fra macOS.")
        except Exception as e:
            messagebox.showerror("Feil", f"Kunne ikke lese databasen:\n{e}")

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

    def _status(self, msg):
        self.status_var.set(msg)

    def _selected_pk(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def _selected_item(self):
        pk = self._selected_pk()
        if pk is None:
            return None
        return next((i for i in self.items if i["pk"] == pk), None)

    # ── Token batch-erstatt ────────────────────────────────────────────────────
    def _on_token_click(self, event=None):
        idx = self.token_list.curselection()
        if not idx:
            return
        token, count = self._tokens[idx[0]]
        dlg = BatchReplaceDialog(self, token, count)
        if not dlg.result:
            return
        new_val  = dlg.result
        affected = [i for i in self.items if token in i.get("phrase", "")]
        backup()
        for item in affected:
            new_phrase = item["phrase"].replace(token, new_val)
            update_item(item["pk"], item["shortcut"], new_phrase)
            item["phrase"] = new_phrase
        restart_keyboard_daemon()
        self._refresh_table()
        self._refresh_tokens()
        self._status(f"✓ Erstattet «{token}» → «{new_val}» i {len(affected)} fraser.")

    # ── CRUD ───────────────────────────────────────────────────────────────────
    def _add(self):
        dlg = EditDialog(self, title="Ny snarvei")
        if not dlg.result:
            return
        sc, ph = dlg.result
        if any(i["shortcut"] == sc for i in self.items):
            messagebox.showerror("Finnes allerede", f"'{sc}' er allerede i bruk.")
            return
        backup()
        insert_item(sc, ph)
        restart_keyboard_daemon()
        self._load()
        self._status(f"✓ La til '{sc}'.")

    def _edit_selected(self):
        item = self._selected_item()
        if not item:
            messagebox.showinfo("Velg rad", "Klikk på en snarvei i lista først.")
            return
        dlg = EditDialog(self, title="Endre snarvei",
                         shortcut=item["shortcut"], phrase=item["phrase"])
        if not dlg.result:
            return
        backup()
        update_item(item["pk"], dlg.result[0], dlg.result[1])
        restart_keyboard_daemon()
        self._load()
        self._status(f"✓ Endret '{item['shortcut']}'.")

    def _delete_selected(self):
        item = self._selected_item()
        if not item:
            messagebox.showinfo("Velg rad", "Klikk på en snarvei i lista først.")
            return
        if not messagebox.askyesno("Bekreft sletting",
                                   f"Slette snarveien '{item['shortcut']}'?"):
            return
        backup()
        delete_item(item["pk"])
        restart_keyboard_daemon()
        self._load()
        self._status(f"✓ Slettet '{item['shortcut']}'.")

    def _find_replace(self):
        win = tk.Toplevel(self)
        win.title("Finn og erstatt")
        win.configure(bg="white")
        win.resizable(False, False)
        pad = {"padx": 16, "pady": 6}
        for row, lbl in enumerate(["Finn:", "Erstatt med:"]):
            tk.Label(win, text=lbl, bg="white",
                     font=("SF Pro Text", 12)).grid(row=row, column=0, sticky="w", **pad)
        fv, rv = tk.StringVar(), tk.StringVar()
        for row, var in enumerate([fv, rv]):
            tk.Entry(win, textvariable=var, width=40,
                     font=("SF Pro Text", 12)
                     ).grid(row=row, column=1, sticky="ew", **pad)

        def do_replace():
            f, r = fv.get(), rv.get()
            if not f:
                return
            affected = [i for i in self.items if f in i.get("phrase", "")]
            if not affected:
                messagebox.showinfo("Ingen treff", f"Fant ikke '{f}' i noen fraser.")
                return
            backup()
            for item in affected:
                new_phrase = item["phrase"].replace(f, r)
                update_item(item["pk"], item["shortcut"], new_phrase)
            restart_keyboard_daemon()
            self._load()
            self._status(f"✓ Finn/Erstatt: endret {len(affected)} fraser.")
            win.destroy()

        bf = tk.Frame(win, bg="white")
        bf.grid(row=2, column=0, columnspan=2, pady=10)
        tk.Button(bf, text="Erstatt", command=do_replace,
                  bg="#007aff", fg="white", relief="flat",
                  font=("SF Pro Text", 12, "bold"), padx=14).pack(side="left", padx=6)
        tk.Button(bf, text="Avbryt", command=win.destroy,
                  relief="flat", font=("SF Pro Text", 12), padx=14).pack(side="left", padx=6)

# ── Start ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    App().mainloop()