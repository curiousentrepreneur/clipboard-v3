"""Bağımlılıksız klasik arayüz.

CustomTkinter yoksa veya --klasik ile başlatılırsa bu ekran açılır.
Temel hedef: uygulamayı her bilgisayarda çalıştırmak ve çekirdeği test etmek.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pyperclip

from . import core, network


class App:
    def __init__(self, c: core.Core):
        self.core = c
        self.root = tk.Tk()
        self.root.title("Labs Clipboard v0.3")
        self.root.geometry("760x520")
        self.root.minsize(680, 460)
        self._build()
        self.root.protocol("WM_DELETE_WINDOW", self._quit)
        self.root.after(500, self._poll)

    def _build(self):
        pad = {"padx": 10, "pady": 6}
        top = ttk.Frame(self.root)
        top.pack(fill="x", **pad)
        ttk.Label(top, text="Labs Clipboard", font=("Segoe UI", 16, "bold")).pack(side="left")
        ttk.Label(top, text=f"  IP: {network.local_ip()}  FP: {self.core.identity.fingerprint}").pack(side="left")

        row = ttk.Frame(self.root)
        row.pack(fill="x", **pad)
        ttk.Button(row, text="PIN oluştur", command=self._pin).pack(side="left", padx=4)
        ttk.Button(row, text="Cihaza bağlan", command=self._pair_dialog).pack(side="left", padx=4)
        ttk.Button(row, text="Panoyu gönder", command=self._send).pack(side="left", padx=4)
        ttk.Button(row, text="Dosya gönder", command=self._send_file).pack(side="left", padx=4)
        ttk.Button(row, text="Geçmişi temizle", command=self._clear_history).pack(side="left", padx=4)

        mode = ttk.Frame(self.root)
        mode.pack(fill="x", **pad)
        self.mode_var = tk.StringVar(value="local")
        ttk.Radiobutton(mode, text="Bu cihaz", variable=self.mode_var, value="local", command=self._mode).pack(side="left")
        ttk.Radiobutton(mode, text="Tümü", variable=self.mode_var, value="all", command=self._mode).pack(side="left")
        self.sensitive = tk.BooleanVar(value=False)
        ttk.Checkbutton(mode, text="Hassas mod", variable=self.sensitive, command=self._sensitive).pack(side="left", padx=12)
        self.auto_send = tk.BooleanVar(value=True)
        ttk.Checkbutton(mode, text="Otomatik gönder", variable=self.auto_send, command=self._auto).pack(side="left")

        panes = ttk.PanedWindow(self.root, orient="horizontal")
        panes.pack(fill="both", expand=True, **pad)

        left = ttk.Frame(panes)
        right = ttk.Frame(panes)
        panes.add(left, weight=1)
        panes.add(right, weight=2)

        ttk.Label(left, text="Eşleşmiş/çevrimiçi cihazlar").pack(anchor="w")
        self.devices = tk.Listbox(left)
        self.devices.pack(fill="both", expand=True)

        ttk.Label(right, text="Pano geçmişi").pack(anchor="w")
        self.history = tk.Listbox(right)
        self.history.pack(fill="both", expand=True)
        self.history.bind("<Double-Button-1>", self._copy_history)

        self.status = tk.StringVar(value="Hazır")
        ttk.Label(self.root, textvariable=self.status, relief="sunken", anchor="w").pack(fill="x")

    def _mode(self):
        self.core.mode = self.mode_var.get()

    def _sensitive(self):
        self.core.sensitive_mode = bool(self.sensitive.get())

    def _auto(self):
        self.core.auto_send = bool(self.auto_send.get())

    def _pin(self):
        pin = self.core.begin_pairing_host()
        messagebox.showinfo("Eşleştirme PIN", f"Diğer cihaza bu PIN'i gir:\n\n{pin}")

    def _pair_dialog(self):
        win = tk.Toplevel(self.root)
        win.title("Cihaz eşleştir")
        win.resizable(False, False)
        ttk.Label(win, text="Diğer cihazın IP adresi:").grid(row=0, column=0, sticky="w", padx=10, pady=6)
        ip = ttk.Entry(win, width=28)
        ip.grid(row=0, column=1, padx=10, pady=6)
        ttk.Label(win, text="PIN:").grid(row=1, column=0, sticky="w", padx=10, pady=6)
        pin = ttk.Entry(win, width=28)
        pin.grid(row=1, column=1, padx=10, pady=6)

        def go():
            try:
                self.core.pair_with(ip.get().strip(), pin.get().strip())
                self.status.set("Eşleştirme başarılı")
                win.destroy()
            except Exception as e:
                messagebox.showerror("Hata", str(e))

        ttk.Button(win, text="Eşleştir", command=go).grid(row=2, column=0, columnspan=2, pady=10)

    def _send(self):
        try:
            text = pyperclip.paste()
            self.core.send_clipboard(text)
            self.status.set("Pano gönderildi")
        except Exception as e:
            messagebox.showerror("Gönderilemedi", str(e))

    def _send_file(self):
        path = filedialog.askopenfilename()
        if not path:
            return
        try:
            self.core.send_file(path)
            self.status.set("Dosya gönderildi")
        except Exception as e:
            messagebox.showerror("Dosya gönderilemedi", str(e))

    def _clear_history(self):
        self.core.clear_history()
        self._refresh_history()

    def _copy_history(self, _event):
        sel = self.history.curselection()
        if not sel:
            return
        item = self.core.history[sel[0]]
        pyperclip.copy(item.get("text", ""))
        self.status.set("Geçmişten panoya kopyalandı")

    def _refresh_devices(self):
        self.devices.delete(0, tk.END)
        online = self.core.discovery.online
        for fp, p in online.items():
            mark = "✓" if fp in self.core.peers else "•"
            self.devices.insert(tk.END, f"{mark} {p.get('name','?')}  {p.get('ip','?')}  {fp}")

    def _refresh_history(self):
        self.history.delete(0, tk.END)
        for item in self.core.history:
            text = item.get("text", "").replace("\n", " ")
            self.history.insert(tk.END, text[:120])

    def _poll(self):
        self._refresh_devices()
        self._refresh_history()
        while True:
            try:
                ev = self.core.events.get_nowait()
            except Exception:
                break
            self.status.set("Olay: " + " / ".join(map(str, ev)))
        self.root.after(1000, self._poll)

    def _quit(self):
        try:
            self.core.stop()
        except Exception:
            pass
        self.root.destroy()

    def run(self):
        self.root.mainloop()
