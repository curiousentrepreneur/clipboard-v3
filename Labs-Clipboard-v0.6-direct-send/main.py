"""Güvenli Evrensel Pano — giriş noktası.

Kullanım:
    python main.py --ad "Çalışma Bilgisayarı"

customtkinter kuruluysa premium "Obsidiyen Kasa" arayüzü,
değilse klasik Tkinter arayüzü açılır.
"""
import argparse
import socket

from app.core import Core


def main():
    parser = argparse.ArgumentParser(description="Güvenli Evrensel Pano")
    parser.add_argument("--ad", default=socket.gethostname(),
                        help="Bu cihazın görünen adı")
    parser.add_argument("--klasik", action="store_true",
                        help="Klasik arayüzü zorla")
    args = parser.parse_args()

    if args.klasik:
        from app.gui_classic import App
    else:
        try:
            from app.gui import App  # premium (customtkinter gerekir)
        except ImportError:
            from app.gui_classic import App

    core = Core(device_name=args.ad)
    core.start()
    App(core).run()


if __name__ == "__main__":
    main()
