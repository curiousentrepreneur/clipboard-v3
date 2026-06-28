"""Sistem tepsisi ve global kısayol desteği.

Bu modül isteğe bağlı bağımlılıklarla çalışır. pystray/keyboard kurulu değilse
uygulama yine açılır; sadece tepsi ve global kısayol devre dışı kalır.
"""
from __future__ import annotations

HOTKEY = "ctrl+shift+v"


def create_tray(app):
    """Sistem tepsisi simgesi oluşturur. Başarısız olursa None döner."""
    try:
        import threading
        from PIL import Image, ImageDraw
        import pystray

        img = Image.new("RGBA", (64, 64), (11, 13, 18, 255))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((10, 10, 54, 54), radius=10, outline=(201, 138, 91, 255), width=4)
        d.text((24, 20), "L", fill=(236, 239, 247, 255))

        menu = pystray.Menu(
            pystray.MenuItem("Göster", lambda icon, item: app.show()),
            pystray.MenuItem("Panoyu gönder", lambda icon, item: app.send_clipboard_now()),
            pystray.MenuItem("Çık", lambda icon, item: app.quit_app()),
        )
        icon = pystray.Icon("Labs Clipboard", img, "Labs Clipboard", menu)
        threading.Thread(target=icon.run, daemon=True).start()
        return icon
    except Exception:
        return None


def register_hotkey(callback):
    """Global kısayol kaydeder. Başarılıysa True döner."""
    try:
        import keyboard
        keyboard.add_hotkey(HOTKEY, callback)
        return True
    except Exception:
        return False
