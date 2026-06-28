"""Pano görsel desteği (isteğe bağlı: pip install Pillow).

- grab_png(): panodaki görseli PNG bayt dizisi olarak alır.
- put_png(): PNG verisini işletim sistemine uygun yöntemle panoya yazar
  (Windows: PowerShell, macOS: osascript, Linux: wl-copy/xclip).
"""
import io
import platform
import shutil
import subprocess
import tempfile

try:
    from PIL import ImageGrab  # noqa: F401
    AVAILABLE = True
except ImportError:
    AVAILABLE = False


def grab_png():
    """Panodaki görseli PNG olarak döndürür; görsel yoksa None."""
    if not AVAILABLE:
        return None
    from PIL import ImageGrab
    try:
        img = ImageGrab.grabclipboard()
    except Exception:
        return None
    if img is None or not hasattr(img, "save"):
        return None  # panoda görsel değil (metin veya dosya listesi)
    buf = io.BytesIO()
    img.convert("RGBA").save(buf, "PNG")
    return buf.getvalue()


def put_png(data: bytes) -> bool:
    """PNG verisini panoya yazar. Başarı durumunu döndürür."""
    system = platform.system()
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(data)
        path = f.name
    try:
        if system == "Windows":
            ps = (
                "Add-Type -AssemblyName System.Windows.Forms; "
                "Add-Type -AssemblyName System.Drawing; "
                f"$img=[System.Drawing.Image]::FromFile('{path}'); "
                "[System.Windows.Forms.Clipboard]::SetImage($img); "
                "$img.Dispose()"
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-STA", "-Command", ps],
                check=True, capture_output=True, timeout=15,
            )
        elif system == "Darwin":
            script = (f'set the clipboard to '
                      f'(read (POSIX file "{path}") as \u00abclass PNGf\u00bb)')
            subprocess.run(["osascript", "-e", script],
                           check=True, capture_output=True, timeout=15)
        else:  # Linux
            if shutil.which("wl-copy"):
                with open(path, "rb") as fh:
                    subprocess.run(["wl-copy", "-t", "image/png"],
                                   stdin=fh, check=True, timeout=15)
            elif shutil.which("xclip"):
                subprocess.run(
                    ["xclip", "-selection", "clipboard",
                     "-t", "image/png", "-i", path],
                    check=True, capture_output=True, timeout=15,
                )
            else:
                return False
        return True
    except Exception:
        return False
