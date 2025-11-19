import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import time
from datetime import datetime, date
import platform

# ---------- Sound alert ----------
def play_alert_sound():
    system = platform.system()
    if system == "Windows":
        try:
            import winsound
            for i in range(3):
                winsound.Beep(2000, 500)
                time.sleep(0.25)
        except Exception as e:
            print("Windows sound failed:", e)
    else:
        try:
            from playsound import playsound
            # Make sure alert.mp3 is in the same folder or give full path
            playsound("alert.mp3")
        except Exception as e:
            print("⚠ Sound failed — install playsound or add an alert.mp3 file. Error:", e)

# ---------- Reminder app ----------
class MedicineReminderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Medicine Reminder (Multiple Alerts Per Day)")
        self.geometry("700x450")
        self.resizable(False, False)

        # data structures
        # reminders: {medicine_name: [ "HH:MM", ... ] }
        self.reminders = {}
        # already alerted this day: set of (medicine, "HH:MM")
        self.already_alerted = set()
        self.current_date = date.today()

        # UI
        self.create_widgets()

        # control
        self.running = False
        self.check_interval_ms = 10 * 1000  # check every 10 seconds

    def create_widgets(self):
        # Top frame for adding
        frm_top = tk.Frame(self, padx=10, pady=10)
        frm_top.pack(fill="x")

        tk.Label(frm_top, text="Medicine name:").grid(row=0, column=0, sticky="w")
        self.entry_name = tk.Entry(frm_top, width=25)
        self.entry_name.grid(row=0, column=1, padx=6)

        tk.Label(frm_top, text="Time (HH:MM):").grid(row=0, column=2, sticky="w")
        self.entry_time = tk.Entry(frm_top, width=12)
        self.entry_time.grid(row=0, column=3, padx=6)

        btn_add = tk.Button(frm_top, text="Add time", command=self.add_time)
        btn_add.grid(row=0, column=4, padx=6)

        btn_clear = tk.Button(frm_top, text="Clear fields", command=self.clear_fields)
        btn_clear.grid(row=0, column=5, padx=6)

        # Middle frame: Treeview to show reminders
        frm_mid = tk.Frame(self, padx=10, pady=10)
        frm_mid.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(frm_mid, columns=("medicine", "time"), show="headings", height=12)
        self.tree.heading("medicine", text="Medicine")
        self.tree.heading("time", text="Time (HH:MM)")
        self.tree.column("medicine", width=300)
        self.tree.column("time", width=120, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(frm_mid, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscroll=scrollbar.set)

        # Bottom frame: controls
        frm_bottom = tk.Frame(self, padx=10, pady=10)
        frm_bottom.pack(fill="x")

        btn_remove = tk.Button(frm_bottom, text="Remove selected", command=self.remove_selected)
        btn_remove.pack(side="left", padx=4)

        btn_start = tk.Button(frm_bottom, text="Start reminders", command=self.start_reminders)
        btn_start.pack(side="left", padx=4)

        btn_stop = tk.Button(frm_bottom, text="Stop reminders", command=self.stop_reminders)
        btn_stop.pack(side="left", padx=4)

        btn_import = tk.Button(frm_bottom, text="Import from text file", command=self.import_from_file)
        btn_import.pack(side="right", padx=4)

        btn_export = tk.Button(frm_bottom, text="Export to text file", command=self.export_to_file)
        btn_export.pack(side="right", padx=4)

        # status
        self.status_var = tk.StringVar(value="Stopped")
        lbl_status = tk.Label(self, textvariable=self.status_var, anchor="w")
        lbl_status.pack(fill="x", padx=10, pady=(0,10))

    def add_time(self):
        name = self.entry_name.get().strip()
        t = self.entry_time.get().strip()

        if not name:
            messagebox.showwarning("Input error", "Enter medicine name.")
            return
        if not self.validate_time(t):
            messagebox.showwarning("Input error", "Enter time in HH:MM format (24-hour).")
            return

        # add
        times = self.reminders.get(name, [])
        if t in times:
            messagebox.showinfo("Info", f"Time {t} already exists for {name}.")
            return
        times.append(t)
        # keep times sorted for readability
        times.sort()
        self.reminders[name] = times

        self.refresh_tree()
        self.clear_fields()

    def clear_fields(self):
        self.entry_name.delete(0, tk.END)
        self.entry_time.delete(0, tk.END)

    def validate_time(self, t):
        try:
            if len(t) != 5: return False
            hh, mm = t.split(":")
            hh = int(hh); mm = int(mm)
            return 0 <= hh <= 23 and 0 <= mm <= 59
        except Exception:
            return False

    def refresh_tree(self):
        # clear
        for item in self.tree.get_children():
            self.tree.delete(item)
        # insert
        for med, times in sorted(self.reminders.items()):
            for tm in times:
                self.tree.insert("", "end", values=(med, tm))

    def remove_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Select a reminder to remove.")
            return
        for item in sel:
            med, tm = self.tree.item(item, "values")
            if med in self.reminders and tm in self.reminders[med]:
                self.reminders[med].remove(tm)
                if not self.reminders[med]:
                    del self.reminders[med]
        self.refresh_tree()

    def start_reminders(self):
        if self.running:
            messagebox.showinfo("Info", "Reminders already running.")
            return
        if not self.reminders:
            messagebox.showwarning("Warning", "No reminders set.")
            return
        self.running = True
        self.status_var.set("Running — checking every {} seconds".format(self.check_interval_ms//1000))
        self.after(1000, self.check_loop)  # start after 1 second

    def stop_reminders(self):
        if not self.running:
            messagebox.showinfo("Info", "Reminders are not running.")
            return
        self.running = False
        self.status_var.set("Stopped")

    def check_loop(self):
        # If stopped, do nothing
        if not self.running:
            return

        # Reset already_alerted on date change
        today = date.today()
        if today != self.current_date:
            self.current_date = today
            self.already_alerted.clear()

        now = datetime.now().strftime("%H:%M")
        # iterate
        for med, times in self.reminders.items():
            for t in times:
                key = (med, t)
                if now == t and key not in self.already_alerted:
                    # show popup and beep
                    try:
                        messagebox.showinfo("Medicine Alert", f"⏰ Time to take your medicine:\n\n{med}  —  {t}")
                    except Exception:
                        print(f"ALERT: {med} at {t}")
                    # play sound (non-blocking-ish): keep it simple
                    play_alert_sound()
                    self.already_alerted.add(key)

        # schedule next check
        self.after(self.check_interval_ms, self.check_loop)

    def import_from_file(self):
        # Expected file format: each line "medicine,HH:MM" or "medicine,HH:MM;HH:MM;..."
        fname = simpledialog.askstring("Import", "Enter filename to import (e.g. reminders.txt):")
        if not fname:
            return
        try:
            with open(fname, "r", encoding="utf8") as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    parts = line.split(",")
                    med = parts[0].strip()
                    if len(parts) < 2: continue
                    times_part = ",".join(parts[1:]).strip()
                    # allow semicolon-separated or comma separated times
                    items = [x.strip() for x in times_part.replace(";",",").split(",") if x.strip()]
                    valid_times = [t for t in items if self.validate_time(t)]
                    if not valid_times:
                        continue
                    existing = self.reminders.get(med, [])
                    for vt in valid_times:
                        if vt not in existing:
                            existing.append(vt)
                    existing.sort()
                    self.reminders[med] = existing
            self.refresh_tree()
            messagebox.showinfo("Import", "Import finished.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import: {e}")

    def export_to_file(self):
        fname = simpledialog.askstring("Export", "Enter filename to export (e.g. reminders.txt):")
        if not fname:
            return
        try:
            with open(fname, "w", encoding="utf8") as f:
                for med, times in sorted(self.reminders.items()):
                    f.write(med + "," + ";".join(times) + "\n")
            messagebox.showinfo("Export", "Export finished.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")

if __name__ == "__main__":
    app = MedicineReminderApp()
    app.mainloop()
