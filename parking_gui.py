"""
SmartPark Tkinter GUI connected to the single-file C++ backend.

1. Compile smart_parking_backend.cpp to parking_backend.exe.
2. Put parking_backend.exe in the same folder as this Python file.
3. Run: python parking_gui.py

The Python GUI talks to the C++ process using line-based stdin/stdout commands.
The C++ process stays running, so its in-memory data structures remain available
while the GUI is open.
"""

import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

BG = "#0b1220"
SIDEBAR = "#0d1626"
PANEL = "#111d2e"
PANEL_DARK = "#0f1a2a"
LINE = "#26364b"
TEXT = "#edf3fb"
MUTED = "#91a1b7"
BLUE = "#6aa8ff"
GREEN = "#55d6a0"
ORANGE = "#ffbd75"
RED = "#ff8585"


class SmartParkingGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SmartPark | Parking Management System")
        self.geometry("1240x780")
        self.minsize(980, 650)
        self.configure(bg=BG)
        self.backend = None
        self._start_backend()
        self._configure_styles()
        self._build_layout()
        self.refresh_data()

    def _start_backend(self):
        exe = Path(__file__).resolve().with_name("parking_backend.exe")
        if not exe.exists():
            messagebox.showerror(
                "C++ backend not found",
                "Could not find parking_backend.exe.\n\n"
                "Compile smart_parking_backend.cpp and place parking_backend.exe "
                "in the same folder as parking_gui.py."
            )
            self.after(100, self.destroy)
            return
        try:
            self.backend = subprocess.Popen(
                [str(exe)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
                cwd=str(exe.parent)
            )
        except OSError as exc:
            messagebox.showerror("Backend launch failed", str(exc))
            self.after(100, self.destroy)

    def _command(self, command):
        if not self.backend or self.backend.poll() is not None:
            raise RuntimeError("The C++ backend is not running.")
        self.backend.stdin.write(command.replace("\n", " ").replace("\r", " ") + "\n")
        self.backend.stdin.flush()
        response = self.backend.stdout.readline()
        if not response:
            raise RuntimeError("The C++ backend stopped unexpectedly.")
        return response.rstrip("\r\n")

    def _configure_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", background=PANEL_DARK, fieldbackground=PANEL_DARK,
                        foreground=TEXT, rowheight=36, borderwidth=0,
                        font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background="#17263a", foreground="#aebed1",
                        font=("Segoe UI", 9, "bold"), relief="flat", padding=9)
        style.map("Treeview", background=[("selected", "#23466b")],
                  foreground=[("selected", "#ffffff")])

    def _build_layout(self):
        sidebar = tk.Frame(self, bg=SIDEBAR, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        brand = tk.Frame(sidebar, bg=SIDEBAR)
        brand.pack(fill="x", padx=18, pady=(25, 38))
        tk.Label(brand, text="P", bg="#4e8df7", fg="#071427",
                 font=("Segoe UI", 20, "bold"), width=2).pack(side="left", padx=(0, 9))
        labels = tk.Frame(brand, bg=SIDEBAR)
        labels.pack(side="left")
        tk.Label(labels, text="SmartPark", bg=SIDEBAR, fg=TEXT,
                 font=("Segoe UI", 16, "bold")).pack(anchor="w")
        tk.Label(labels, text="C++ PARKING SYSTEM", bg=SIDEBAR, fg="#8091a8",
                 font=("Segoe UI", 8)).pack(anchor="w")
        tk.Label(sidebar, text="WORKSPACE", bg=SIDEBAR, fg="#7e91aa",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=22, pady=(0, 10))
        self._button(sidebar, "▦   Dashboard", self.refresh_data, SIDEBAR, TEXT).pack(fill="x", padx=12, pady=3)
        self._button(sidebar, "＋   Register vehicle", lambda: self.number_entry.focus_set(),
                     SIDEBAR, TEXT).pack(fill="x", padx=12, pady=3)
        self._button(sidebar, "▤   Parked vehicles", lambda: self.search_var.set(""),
                     SIDEBAR, TEXT).pack(fill="x", padx=12, pady=3)
        tk.Frame(sidebar, bg=SIDEBAR).pack(fill="both", expand=True)
        tk.Label(sidebar, text="Python Tkinter UI\nConnected to C++ data structures",
                 bg=SIDEBAR, fg="#718198", font=("Segoe UI", 9),
                 justify="left").pack(anchor="w", padx=17, pady=18)

        main = tk.Frame(self, bg=BG)
        main.pack(side="left", fill="both", expand=True)
        header = tk.Frame(main, bg=BG)
        header.pack(fill="x", padx=28, pady=(25, 20))
        title_box = tk.Frame(header, bg=BG)
        title_box.pack(side="left")
        tk.Label(title_box, text="PARKING OPERATIONS", bg=BG, fg="#7e91aa",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(title_box, text="Dashboard", bg=BG, fg=TEXT,
                 font=("Segoe UI", 27, "bold")).pack(anchor="w", pady=(4, 0))
        tk.Label(title_box, text="Manage your parking lot in one place.",
                 bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(3, 0))
        self._button(header, "↻  Refresh", self.refresh_data, "#111d2c", TEXT).pack(side="right")

        stats = tk.Frame(main, bg=BG)
        stats.pack(fill="x", padx=28, pady=(0, 18))
        for i in range(3):
            stats.grid_columnconfigure(i, weight=1, uniform="stats")
        self.total_value = self._stat(stats, 0, "TOTAL SPACES", BLUE)
        self.occupied_value = self._stat(stats, 1, "OCCUPIED SPACES", ORANGE)
        self.available_value = self._stat(stats, 2, "AVAILABLE SPACES", GREEN)

        content = tk.Frame(main, bg=BG)
        content.pack(fill="both", expand=True, padx=28, pady=(0, 18))
        content.grid_columnconfigure(0, weight=1, minsize=260)
        content.grid_columnconfigure(1, weight=2, minsize=420)
        content.grid_rowconfigure(0, weight=1)

        left = tk.Frame(content, bg=PANEL, highlightbackground=LINE, highlightthickness=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        tk.Label(left, text="Register a vehicle", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=18, pady=(18, 5))
        tk.Label(left, text="Details are processed by the C++ backend.",
                 bg=PANEL, fg=MUTED, font=("Segoe UI", 9), wraplength=270).pack(anchor="w", padx=18, pady=(0, 18))

        form = tk.Frame(left, bg=PANEL)
        form.pack(fill="x", padx=18)
        self.number_entry = self._labeled_entry(form, "Registration number")
        self.owner_entry = self._labeled_entry(form, "Owner name")
        tk.Label(form, text="Vehicle type", bg=PANEL, fg="#c2cddd",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(12, 6))
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(form, textvariable=self.type_var,
                                        values=("Car", "Bike", "Scooter", "SUV", "Other"),
                                        state="readonly")
        self.type_combo.pack(fill="x", ipady=4, pady=(0, 16))
        self._button(form, "Register vehicle  →", self.add_vehicle, BLUE, "#071528").pack(fill="x")
        self.message = tk.Label(form, text="", bg=PANEL, fg=MUTED,
                                font=("Segoe UI", 9), wraplength=270, justify="left")
        self.message.pack(anchor="w", pady=(12, 0))

        right = tk.Frame(content, bg=PANEL, highlightbackground=LINE, highlightthickness=1)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        head = tk.Frame(right, bg=PANEL)
        head.pack(fill="x", padx=16, pady=(18, 12))
        tk.Label(head, text="Parked vehicles", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 14, "bold")).pack(side="left")
        self.vehicle_count = tk.Label(head, text="0 vehicles", bg="#17263a", fg="#b8c9df",
                                      font=("Segoe UI", 9, "bold"), padx=8, pady=5)
        self.vehicle_count.pack(side="right")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.render_table())
        search = tk.Entry(right, textvariable=self.search_var, bg=PANEL_DARK, fg=TEXT,
                          insertbackground=TEXT, relief="flat",
                          highlightthickness=1, highlightbackground="#2b3b50")
        search.pack(fill="x", padx=16, pady=(0, 12), ipady=8)
        table = tk.Frame(right, bg=PANEL)
        table.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.tree = ttk.Treeview(table, columns=("number", "owner", "type", "slot"),
                                 show="headings", height=12)
        for col, title, width in [
            ("number", "REGISTRATION", 125), ("owner", "OWNER", 130),
            ("type", "TYPE", 80), ("slot", "SLOT", 65)
        ]:
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, minwidth=55, anchor="w")
        scroll = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        actions = tk.Frame(main, bg=BG)
        actions.pack(fill="x", padx=28, pady=(0, 16))
        self._button(actions, "Vehicle Exit", self.exit_vehicle, "#3b2b20", ORANGE).pack(side="left", padx=(0, 8))
        self._button(actions, "Search Selected / Enter Number", self.search_vehicle, "#172940", TEXT).pack(side="left", padx=(0, 8))
        self._button(actions, "Waiting Queue", self.show_queue, "#172940", TEXT).pack(side="left", padx=(0, 8))
        self._button(actions, "Vacated Slots Stack", self.show_stack, "#172940", TEXT).pack(side="left")

    def _button(self, parent, text, command, bg, fg):
        return tk.Button(parent, text=text, command=command, bg=bg, fg=fg,
                         activebackground="#244264", activeforeground=TEXT,
                         relief="flat", bd=0, padx=12, pady=10,
                         font=("Segoe UI", 9, "bold"), cursor="hand2")

    def _stat(self, parent, column, title, color):
        card = tk.Frame(parent, bg=PANEL, highlightbackground=LINE, highlightthickness=1)
        card.grid(row=0, column=column, sticky="ew", padx=(0, 8) if column < 2 else (8, 0))
        tk.Label(card, text=title, bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(14, 4))
        value = tk.Label(card, text="—", bg=PANEL, fg=color,
                         font=("Segoe UI", 25, "bold"))
        value.pack(anchor="w", padx=16, pady=(0, 13))
        return value

    def _labeled_entry(self, parent, label):
        tk.Label(parent, text=label, bg=PANEL, fg="#c2cddd",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 6))
        entry = tk.Entry(parent, bg=PANEL_DARK, fg=TEXT, insertbackground=TEXT,
                         relief="flat", highlightthickness=1,
                         highlightbackground="#2b3b50")
        entry.pack(fill="x", ipady=9)
        entry.pack_configure(pady=(0, 12))
        return entry

    def _read_list(self, response, prefix):
        if not response.startswith(prefix + "|"):
            return []
        payload = response.split("|", 1)[1]
        if not payload:
            return []
        return [row.split(",") for row in payload.split(";") if row]

    def refresh_data(self):
        if not self.backend or self.backend.poll() is not None:
            return
        try:
            status = self._command("STATUS").split("|")
            if status[0] == "STATUS":
                self.total_value.config(text=status[1])
                self.occupied_value.config(text=status[2])
                self.available_value.config(text=status[3])
            response = self._command("LIST")
            self.vehicles = []
            for row in self._read_list(response, "LIST"):
                if len(row) >= 4:
                    self.vehicles.append({
                        "number": row[0], "owner": row[1],
                        "type": row[2], "slot": row[3]
                    })
            self.vehicle_count.config(
                text=f"{len(self.vehicles)} {'vehicle' if len(self.vehicles) == 1 else 'vehicles'}"
            )
            self.render_table()
        except Exception as exc:
            self.message.config(text=f"Backend error: {exc}", fg=RED)

    def render_table(self):
        if not hasattr(self, "tree"):
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        query = self.search_var.get().strip().lower()
        for v in getattr(self, "vehicles", []):
            if query and query not in " ".join(v.values()).lower():
                continue
            self.tree.insert("", "end", values=(v["number"], v["owner"], v["type"], v["slot"]))

    def add_vehicle(self):
        number = self.number_entry.get().strip().upper().replace(" ", "")
        owner = self.owner_entry.get().strip()
        kind = self.type_var.get().strip()
        if not number or not owner or not kind:
            self.message.config(text="Please fill in all fields.", fg=RED)
            return
        # Protocol fields use | as separators.
        if any(ch in value for value in (number, owner, kind) for ch in "|\r\n"):
            self.message.config(text="Please remove | or line breaks from the fields.", fg=RED)
            return
        try:
            response = self._command(f"ADD|{number}|{owner}|{kind}")
            parts = response.split("|", 1)
            ok = parts[0] == "OK"
            message = parts[1] if len(parts) > 1 else response
            self.message.config(text=message, fg=GREEN if ok else RED)
            if ok:
                self.number_entry.delete(0, "end")
                self.owner_entry.delete(0, "end")
                self.type_var.set("")
                self.refresh_data()
        except Exception as exc:
            self.message.config(text=str(exc), fg=RED)

    def _selected_number(self):
        selection = self.tree.selection()
        if selection:
            return str(self.tree.item(selection[0], "values")[0])
        return self.number_entry.get().strip().upper().replace(" ", "")

    def exit_vehicle(self):
        number = self._selected_number()
        if not number:
            messagebox.showinfo("Vehicle exit", "Select a vehicle row or enter its registration number.")
            return
        try:
            response = self._command(f"EXIT|{number}")
            parts = response.split("|", 1)
            ok = parts[0] == "OK"
            message = parts[1] if len(parts) > 1 else response
            (messagebox.showinfo if ok else messagebox.showerror)("Vehicle exit", message)
            self.refresh_data()
        except Exception as exc:
            messagebox.showerror("Backend error", str(exc))

    def search_vehicle(self):
        number = self._selected_number()
        if not number:
            messagebox.showinfo("Search vehicle", "Select a vehicle row or enter a registration number.")
            return
        try:
            response = self._command(f"SEARCH|{number}")
            parts = response.split("|")
            if parts[0] == "FOUND" and len(parts) >= 5:
                messagebox.showinfo(
                    "Vehicle found",
                    f"Registration: {parts[1]}\nOwner: {parts[2]}\nType: {parts[3]}\nSlot: {parts[4]}"
                )
            else:
                messagebox.showerror("Search vehicle", parts[1] if len(parts) > 1 else response)
        except Exception as exc:
            messagebox.showerror("Backend error", str(exc))

    def show_queue(self):
        try:
            rows = self._read_list(self._command("QUEUE"), "QUEUE")
            text = "\n".join(f"{i}. {r[0]} | {r[1]} | {r[2]}" for i, r in enumerate(rows, 1))
            messagebox.showinfo("Waiting Queue (FIFO)", text or "No vehicles waiting.")
        except Exception as exc:
            messagebox.showerror("Backend error", str(exc))

    def show_stack(self):
        try:
            response = self._command("STACK")
            payload = response.split("|", 1)[1] if "|" in response else ""
            slots = payload.split(";") if payload else []
            messagebox.showinfo("Recently Vacated Slots (LIFO)", "\n".join(slots) or "No slots in the stack.")
        except Exception as exc:
            messagebox.showerror("Backend error", str(exc))

    def on_close(self):
        if self.backend and self.backend.poll() is None:
            try:
                self.backend.stdin.write("QUIT\n")
                self.backend.stdin.flush()
                self.backend.wait(timeout=1)
            except Exception:
                self.backend.terminate()
        self.destroy()


if __name__ == "__main__":
    app = SmartParkingGUI()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
