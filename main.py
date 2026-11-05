"""
SMART PARKING SPACE MANAGEMENT SYSTEM - Tkinter GUI

The GUI only DRAWS data. All parking logic and all data structures
(Array, Queue, Stack, Hash Table) are in the C++ engine (parking.cpp).

GUI -> engine :  one text line    command|number|owner|type     e.g.  add|MH12AB1234|Rahul|Car
engine -> GUI :  text lines (OK, SLOT, QUEUE, STACK, BUCKET ...) ending with END

Run:  python main.py      (it builds parking.cpp with g++ if needed)
"""
import os
import hashlib
import subprocess
import tempfile
import tkinter as tk
from tkinter import messagebox, ttk

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "parking.cpp")

# ----------------------------------------------------------------- colours and fonts
BG, PANEL, INK, MUTED = "#f4f6fa", "#ffffff", "#1f2937", "#6b7280"
GREEN_BG, GREEN_LN = "#d1fae5", "#10b981"
RED_BG, RED_LN = "#fee2e2", "#ef4444"
BLUE_BG, BLUE_LN = "#dbeafe", "#3b82f6"
AMBER_BG, AMBER_LN = "#fef3c7", "#f59e0b"
PURPLE_BG, PURPLE_LN = "#ede9fe", "#8b5cf6"
FONT = ("Segoe UI", 10)
FONT_B = ("Segoe UI", 10, "bold")
FONT_S = ("Segoe UI", 8)
MONO = ("Consolas", 9)


# =====================================================================
#  Talking to the C++ engine
# =====================================================================
def start_engine():
    """Build a source-specific engine executable, then start it."""
    with open(SRC, "rb") as source:
        source_hash = hashlib.sha256(source.read()).hexdigest()
    exe_name = f"smart-parking-{source_hash}"
    if os.name == "nt":
        exe_name += ".exe"
    exe_path = os.path.join(tempfile.gettempdir(), exe_name)

    if not os.path.exists(exe_path):
        result = subprocess.run(["g++", "-std=c++17", SRC, "-o", exe_path], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError("Could not build parking.cpp:\n" + result.stderr[:1500])
    return subprocess.Popen([exe_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            text=True, encoding="utf-8", bufsize=1)


def read_reply(stream):
    """Read the engine's text lines until END and return them as a dictionary."""
    reply = {"ok": True, "message": "", "slot": "", "bucket": -1,
             "slots": [], "queue": [], "stack": [], "hash": []}
    while True:
        raw = stream.readline()
        if raw == "":
            raise RuntimeError("The C++ engine stopped")
        parts = raw.rstrip("\n").split("|")
        kind = parts[0]
        if kind in ("OK", "ERR"):
            reply["ok"] = (kind == "OK")
            reply["message"] = "|".join(parts[1:])
        elif kind == "HIGHLIGHT":
            reply["slot"], reply["bucket"] = parts[1], int(parts[2])
        elif kind == "SLOT":                                   # SLOT|P01|MH12AB1234  (empty = free)
            reply["slots"].append({"id": parts[1], "occ": parts[2] != "", "veh": parts[2]})
        elif kind == "QUEUE":                                  # QUEUE|number|owner|type
            reply["queue"].append({"no": parts[1], "owner": parts[2], "type": parts[3]})
        elif kind == "STACK":                                  # STACK|P02   (top first)
            reply["stack"].append(parts[1])
        elif kind == "BUCKET":                                 # BUCKET|3|MH12AB1234,P01|...
            chain = []
            for item in parts[2:]:
                number, slot = item.split(",")
                chain.append({"no": number, "slot": slot})
            reply["hash"].append(chain)
        elif kind == "END":
            total = len(reply["slots"])
            occupied = sum(1 for s in reply["slots"] if s["occ"])
            reply["stats"] = {"total": total, "occupied": occupied, "free": total - occupied,
                              "waiting": len(reply["queue"]),
                              "records": sum(len(c) for c in reply["hash"]),
                              "tableSize": len(reply["hash"])}
            return reply


# =====================================================================
#  Main window
# =====================================================================
class ParkingApp(tk.Tk):
    SLOT_W, SLOT_H, SLOT_PAD, SLOTS_PER_ROW = 76, 58, 6, 10

    def __init__(self):
        super().__init__()
        self.title("Smart Parking Space Management System - Data Structures")
        self.geometry("1300x780")
        self.minsize(1150, 720)
        self.configure(bg=BG)

        try:
            self.engine = start_engine()
        except Exception as error:
            messagebox.showerror("Engine error", str(error))
            self.destroy()
            raise SystemExit(1)

        self.snap = None          # latest reply from the engine
        self.hl_slot = None       # slot highlighted after a command
        self.hl_bucket = -1       # hash bucket highlighted after a command
        self._flash_job = None

        self._build_ui()
        self.run("status")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------ build the window
    def _card(self, parent, title, accent):
        outer = tk.Frame(parent, bg=PANEL, highlightbackground="#e5e7eb", highlightthickness=1)
        head = tk.Frame(outer, bg=accent)
        head.pack(fill="x")
        tk.Label(head, text=title, bg=accent, fg="white", font=FONT_B, anchor="w",
                 padx=8, pady=3).pack(fill="x")
        return outer

    def _build_ui(self):
        # header with live counters
        header = tk.Frame(self, bg="#111827")
        header.pack(fill="x")
        tk.Label(header, text="SMART PARKING MANAGEMENT SYSTEM", bg="#111827", fg="white",
                 font=("Segoe UI", 14, "bold"), padx=14, pady=8).pack(side="left")
        self.stat_labels = {}
        for key, text, color in [("total", "Total", "#9ca3af"), ("occupied", "Occupied", "#f87171"),
                                 ("free", "Free", "#34d399"), ("waiting", "Waiting", "#fbbf24")]:
            label = tk.Label(header, text=f"{text}: -", bg="#111827", fg=color, font=FONT_B, padx=12)
            label.pack(side="right")
            self.stat_labels[key] = (label, text)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=8, pady=8)
        left = tk.Frame(body, bg=BG, width=300)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)
        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        # ---- controls (left)
        card = self._card(left, "VEHICLE CONTROLS", "#374151")
        card.pack(fill="x")
        form = tk.Frame(card, bg=PANEL, padx=10, pady=8)
        form.pack(fill="x")
        self.var_no, self.var_owner, self.var_type = tk.StringVar(), tk.StringVar(), tk.StringVar(value="Car")

        tk.Label(form, text="Vehicle number", bg=PANEL, fg=MUTED, font=FONT_S).pack(anchor="w")
        entry_no = tk.Entry(form, textvariable=self.var_no, font=FONT)
        entry_no.pack(fill="x", pady=(0, 6))
        tk.Label(form, text="Owner name", bg=PANEL, fg=MUTED, font=FONT_S).pack(anchor="w")
        entry_owner = tk.Entry(form, textvariable=self.var_owner, font=FONT)
        entry_owner.pack(fill="x", pady=(0, 6))
        tk.Label(form, text="Vehicle type", bg=PANEL, fg=MUTED, font=FONT_S).pack(anchor="w")
        ttk.Combobox(form, textvariable=self.var_type, state="readonly", font=FONT,
                     values=["Car", "Bike", "Truck", "Other"]).pack(fill="x", pady=(0, 8))
        entry_no.bind("<Return>", lambda e: self.on_add())
        entry_owner.bind("<Return>", lambda e: self.on_add())

        def button(text, color, command):
            tk.Button(form, text=text, command=command, bg=color, fg="white", activebackground=color,
                      relief="flat", font=FONT_B, pady=4, cursor="hand2").pack(fill="x", pady=2)

        button("Add Vehicle  (Allocate Parking)", "#059669", self.on_add)
        button("Vehicle Exit", "#dc2626", self.on_exit)
        button("Search Vehicle (Hash Table)", "#2563eb", self.on_search)
        button("Load Demo Data", "#7c3aed", self.on_demo)
        button("Reset System", "#6b7280", self.on_reset)

        self.status = tk.Label(form, text="Ready", bg=PANEL, fg=INK, font=FONT, wraplength=260,
                               justify="left", anchor="w")
        self.status.pack(fill="x", pady=(8, 0))

        # ---- ARRAY panel
        slot_card = self._card(right, "ARRAY  -  parking slots  (slots[i] access / update: O(1))", "#0f766e")
        slot_card.pack(fill="x")
        width = self.SLOT_PAD + self.SLOTS_PER_ROW * (self.SLOT_W + self.SLOT_PAD)
        self.c_slots = tk.Canvas(slot_card, bg=PANEL, width=width, highlightthickness=0,
                                 height=2 * (self.SLOT_H + self.SLOT_PAD) + self.SLOT_PAD)
        self.c_slots.pack(padx=4, pady=4)
        self.c_slots.bind("<Button-1>", self._on_slot_click)

        # ---- QUEUE and STACK panels
        middle = tk.Frame(right, bg=BG)
        middle.pack(fill="x", pady=8)
        queue_card = self._card(middle, "QUEUE (FIFO)  -  waiting vehicles   enqueue / dequeue: O(1)", "#1d4ed8")
        queue_card.pack(side="left", fill="both", expand=True)
        self.c_queue = tk.Canvas(queue_card, bg=PANEL, height=215, width=560, highlightthickness=0)
        self.c_queue.pack(fill="both", expand=True, padx=4, pady=4)
        stack_card = self._card(middle, "STACK (LIFO)  -  vacated slots   push / pop: O(1)", "#b45309")
        stack_card.pack(side="left", fill="y", padx=(8, 0))
        self.c_stack = tk.Canvas(stack_card, bg=PANEL, height=215, width=260, highlightthickness=0)
        self.c_stack.pack(padx=4, pady=4)

        # ---- HASH TABLE panel
        hash_card = self._card(right, "HASH TABLE  -  separate chaining   insert / search / delete: O(1) average", "#6d28d9")
        hash_card.pack(fill="both", expand=True)
        self.c_hash = tk.Canvas(hash_card, bg=PANEL, highlightthickness=0, height=270)
        self.c_hash.pack(fill="both", expand=True, padx=4, pady=4)

    # ------------------------------------------------------------ send a command
    def run(self, command):
        """Send one command line to the engine, then redraw everything."""
        try:
            self.engine.stdin.write(command + "\n")
            self.engine.stdin.flush()
            reply = read_reply(self.engine.stdout)
        except Exception as error:
            messagebox.showerror("Engine error", str(error))
            return None
        self.snap = reply
        self.hl_slot = reply["slot"] or None
        self.hl_bucket = reply["bucket"]
        self.refresh()
        self.status.config(text=reply["message"], fg="#047857" if reply["ok"] else "#b91c1c")
        if self._flash_job:
            self.after_cancel(self._flash_job)
        self._flash_job = self.after(2500, self._clear_highlight)   # remove the yellow highlight
        return reply

    def _clear_highlight(self):
        self.hl_slot, self.hl_bucket, self._flash_job = None, -1, None
        self.refresh()

    @staticmethod
    def _clean(text):
        return text.strip().replace("|", " ")      # '|' separates the fields, so remove it from input

    # ------------------------------------------------------------ button actions
    def on_add(self):
        reply = self.run(f"add|{self._clean(self.var_no.get())}|{self._clean(self.var_owner.get())}"
                         f"|{self.var_type.get()}")
        if reply and reply["ok"]:
            self.var_no.set("")
            self.var_owner.set("")

    def on_exit(self):
        reply = self.run(f"exit|{self._clean(self.var_no.get())}")
        if reply and reply["ok"]:
            self.var_no.set("")

    def on_search(self):
        self.run(f"search|{self._clean(self.var_no.get())}")

    def on_reset(self):
        if messagebox.askyesno("Reset", "Remove all vehicles and clear every data structure?"):
            self.run("reset")

    def on_demo(self):
        """Fill every slot, then add 2 waiting vehicles."""
        self.run("reset")
        total = self.snap["stats"]["total"]
        people = [("MH12AA1111", "Amit", "Car"), ("MH12BB2222", "Rahul", "Bike"),
                  ("MH12CC3333", "Sneha", "Car"), ("MH12DD4444", "Rohan", "Bike"),
                  ("MH12EE5555", "Neha", "Car")][:total]
        for i in range(len(people), total):
            people.append((f"MH14XY{1000 + i * 7}", f"Owner {i}", "Car" if i % 2 == 0 else "Bike"))
        people += [("MH12FF6666", "Karan", "Car"), ("MH12GG7777", "Pooja", "Bike")]
        for number, owner, vtype in people:
            self.run(f"add|{number}|{owner}|{vtype}")
        self.status.config(text="Demo loaded: parking is full and 2 vehicles are waiting. "
                                "Now exit MH12BB2222 and watch the stack and the queue.", fg="#1d4ed8")
        self.var_no.set("MH12BB2222")

    def _on_slot_click(self, event):
        """Clicking an occupied slot copies its vehicle number into the box."""
        cell = self.SLOT_W + self.SLOT_PAD
        col = (event.x - self.SLOT_PAD) // cell
        row = (event.y - self.SLOT_PAD) // (self.SLOT_H + self.SLOT_PAD)
        index = row * self.SLOTS_PER_ROW + col
        if 0 <= col < self.SLOTS_PER_ROW and 0 <= index < len(self.snap["slots"]):
            if self.snap["slots"][index]["occ"]:
                self.var_no.set(self.snap["slots"][index]["veh"])

    # ------------------------------------------------------------ drawing
    def refresh(self):
        stats = self.snap["stats"]
        for key, (label, name) in self.stat_labels.items():
            label.config(text=f"{name}: {stats[key]}")
        self._draw_slots()
        self._draw_queue()
        self._draw_stack()
        self._draw_hash()

    def _draw_slots(self):
        c = self.c_slots
        c.delete("all")
        w, h, pad = self.SLOT_W, self.SLOT_H, self.SLOT_PAD
        for i, s in enumerate(self.snap["slots"]):
            row, col = divmod(i, self.SLOTS_PER_ROW)
            x, y = pad + col * (w + pad), pad + row * (h + pad)
            fill, line, width = (RED_BG, RED_LN, 1) if s["occ"] else (GREEN_BG, GREEN_LN, 1)
            if s["id"] == self.hl_slot:
                line, width = AMBER_LN, 4
            c.create_rectangle(x, y, x + w, y + h, fill=fill, outline=line, width=width)
            c.create_text(x + w / 2, y + 14, text=s["id"], font=FONT_B, fill=INK)
            c.create_text(x + w / 2, y + 33, text=s["veh"] if s["occ"] else "FREE",
                          font=FONT_S, fill=INK if s["occ"] else GREEN_LN)
            c.create_text(x + w / 2, y + 48, text=f"slots[{i}]", font=("Consolas", 7), fill=MUTED)

    def _draw_queue(self):
        c = self.c_queue
        c.delete("all")
        items = self.snap["queue"]
        n = len(items)
        c.create_text(10, 14, anchor="w", font=FONT_B, fill=BLUE_LN, text=f"size = {n}")
        if n == 0:
            c.create_text(280, 110, text="Queue is empty\n(vehicles wait here when parking is full)",
                          font=FONT, fill=MUTED, justify="center")
            return
        bw, bh, gap, y = 96, 74, 28, 70
        show = min(n, 4)
        for i in range(show):
            x = 14 + i * (bw + gap)
            v = items[i]
            c.create_rectangle(x, y, x + bw, y + bh, fill=BLUE_BG, outline=BLUE_LN, width=2)
            c.create_text(x + bw / 2, y + 16, text=v["no"], font=("Segoe UI", 8, "bold"), fill=INK)
            c.create_text(x + bw / 2, y + 36, text=v["owner"][:14], font=FONT_S, fill=INK)
            c.create_text(x + bw / 2, y + 54, text=f"#{i + 1}  {v['type']}", font=FONT_S, fill=MUTED)
            if i < show - 1 or n > show:
                c.create_line(x + bw, y + bh / 2, x + bw + gap, y + bh / 2, arrow="last", fill=BLUE_LN, width=2)
        if n > show:
            x = 14 + show * (bw + gap)
            c.create_text(x + 20, y + bh / 2, text=f"+{n - show}\nmore", font=FONT_B, fill=BLUE_LN)
        c.create_text(14 + bw / 2, y - 14, text="FRONT (dequeue)", font=FONT_S, fill=BLUE_LN)
        c.create_polygon(14 + bw / 2 - 6, y - 6, 14 + bw / 2 + 6, y - 6, 14 + bw / 2, y,
                         fill=BLUE_LN, outline="")
        c.create_text(10, y + bh + 30, anchor="w", font=FONT_S, fill=MUTED,
                      text=f"REAR (enqueue): {items[-1]['no']}   -   first in, first out")

    def _draw_stack(self):
        c = self.c_stack
        c.delete("all")
        items = self.snap["stack"]                      # top first
        n = len(items)
        c.create_text(10, 14, anchor="w", font=FONT_B, fill=AMBER_LN, text=f"size = {n}")
        if n == 0:
            c.create_text(130, 110, text="Stack is empty\n(freed slots appear here)",
                          font=FONT, fill=MUTED, justify="center")
            return
        show, cell_h, x0, y0 = min(n, 6), 26, 70, 36
        for i in range(show):
            y = y0 + i * (cell_h + 4)
            c.create_rectangle(x0, y, x0 + 120, y + cell_h, fill=AMBER_BG, outline=AMBER_LN, width=2)
            c.create_text(x0 + 60, y + cell_h / 2, text=items[i], font=FONT_B, fill=INK)
        c.create_text(x0 - 8, y0 + cell_h / 2, anchor="e", text="TOP >", font=FONT_B, fill=AMBER_LN)
        if n > show:
            c.create_text(x0 + 60, y0 + show * (cell_h + 4) + 8, text=f"... {n - show} more below",
                          font=FONT_S, fill=MUTED)
        c.create_text(130, 205, text="last in, first out", font=FONT_S, fill=MUTED)

    def _draw_hash(self):
        c = self.c_hash
        c.delete("all")
        stats = self.snap["stats"]
        row_h = 22
        c.create_text(8, 10, anchor="w", font=FONT_S, fill=MUTED,
                      text=f"table size = {stats['tableSize']}   records = {stats['records']}   "
                           f"hash(key) = (h*31 + char) % {stats['tableSize']}   collisions are chained")
        for b, chain in enumerate(self.snap["hash"]):
            y = 24 + b * row_h
            if b == self.hl_bucket:
                c.create_rectangle(2, y - 1, 1200, y + row_h - 3, fill=AMBER_BG, outline=AMBER_LN)
            c.create_text(10, y + 9, anchor="w", text=f"[{b:>2}]", font=MONO, fill=PURPLE_LN)
            x = 50
            if not chain:
                c.create_text(x, y + 9, anchor="w", text="None", font=FONT_S, fill=MUTED)
            for i, v in enumerate(chain):
                c.create_rectangle(x, y, x + 150, y + 17, fill=PURPLE_BG, outline=PURPLE_LN)
                c.create_text(x + 75, y + 8, text=f"{v['no']} ({v['slot']})", font=("Consolas", 8), fill=INK)
                x += 150
                c.create_line(x, y + 8, x + 22, y + 8, arrow="last", fill=PURPLE_LN)
                x += 22
                if i == len(chain) - 1:
                    c.create_text(x + 2, y + 8, anchor="w", text="None", font=FONT_S, fill=MUTED)
            if len(chain) > 1:
                c.create_text(x + 40, y + 8, anchor="w", text="<- collision chain", font=FONT_S, fill=RED_LN)

    # ------------------------------------------------------------ close
    def _on_close(self):
        try:
            self.engine.stdin.write("quit\n")
            self.engine.stdin.flush()
        except Exception:
            pass
        self.destroy()


if __name__ == "__main__":
    ParkingApp().mainloop()
