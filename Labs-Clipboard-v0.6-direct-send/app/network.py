"""Ağ katmanı: yerel ağ keşfi ve TCP taşıma.

- Keşif: UDP broadcast ile cihazlar kendilerini duyurur (yalnızca ad ve
  parmak izi — içerik asla yayınlanmaz).
- Taşıma: uzunluk önekli JSON mesajları. Bir bağlantı üzerinden birden
  fazla istek/yanıt taşınabilir (Session) — parçalı dosya aktarımı bunu
  kullanır. İçerik, crypto modülüyle uçtan uca şifrelidir.
- Hiçbir veri yerel ağ dışına veya bir buluta gönderilmez.
"""
import json
import socket
import struct
import threading
import time

DISCOVERY_PORT = 47900
DATA_PORT = 47901
MAGIC = "LABS_CLIPBOARD_V06"
MAX_MESSAGE = 16 * 1024 * 1024  # tek mesaj sınırı (dosyalar parçalı gider)


def local_ip() -> str:
    """Yerel ağ IP adresini bulur."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))  # paket gönderilmez, rota seçilir
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Bağlantı kapandı")
        buf += chunk
    return buf


def _send_obj(sock: socket.socket, obj: dict):
    data = json.dumps(obj).encode()
    sock.sendall(struct.pack(">I", len(data)) + data)


def _recv_obj(sock: socket.socket) -> dict:
    (length,) = struct.unpack(">I", _recv_exact(sock, 4))
    if length > MAX_MESSAGE:
        raise ValueError("Mesaj çok büyük")
    return json.loads(_recv_exact(sock, length))


class Session:
    """Tek bir cihaza açılan, birden çok istek/yanıt taşıyabilen bağlantı."""

    def __init__(self, ip: str, timeout: float = 10.0):
        self.ip = ip
        self.sock = socket.create_connection((ip, DATA_PORT), timeout=timeout)

    def request(self, obj: dict) -> dict:
        _send_obj(self.sock, obj)
        return _recv_obj(self.sock)

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def send_message(ip: str, obj: dict, timeout: float = 5.0) -> dict:
    """Tek mesaj gönderir ve yanıtı döndürür."""
    with Session(ip, timeout=timeout) as s:
        return s.request(obj)


class Server(threading.Thread):
    """Gelen bağlantıları dinler; bağlantı başına birden çok mesajı işler."""

    def __init__(self, handler):
        super().__init__(daemon=True)
        self.handler = handler  # handler(msg, ip) -> yanıt dict
        self._stop = threading.Event()

    def run(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", DATA_PORT))
        srv.listen(8)
        srv.settimeout(1.0)
        while not self._stop.is_set():
            try:
                conn, addr = srv.accept()
            except socket.timeout:
                continue
            threading.Thread(
                target=self._handle, args=(conn, addr[0]), daemon=True
            ).start()
        srv.close()

    def _handle(self, conn: socket.socket, ip: str):
        try:
            with conn:
                conn.settimeout(60.0)
                while True:  # aynı bağlantıda art arda mesajlar (dosya parçaları)
                    msg = _recv_obj(conn)
                    reply = self.handler(msg, ip)
                    _send_obj(conn, reply or {"ok": True})
        except Exception:
            pass  # bağlantı kapandı veya bozuk/yetkisiz mesaj — sessizce bitir

    def stop(self):
        self._stop.set()


class Discovery(threading.Thread):
    """Yerel ağda cihaz keşfi (UDP broadcast)."""

    def __init__(self, name: str, fingerprint: str):
        super().__init__(daemon=True)
        self.name = name
        self.fingerprint = fingerprint
        self.online = {}  # fp -> {"name", "ip", "ts"}
        self._stop = threading.Event()

    def run(self):
        rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        rx.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        rx.bind(("", DISCOVERY_PORT))
        rx.settimeout(1.0)

        tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        tx.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        last_announce = 0.0
        payload = json.dumps(
            {"magic": MAGIC, "name": self.name, "fp": self.fingerprint}
        ).encode()

        while not self._stop.is_set():
            now = time.time()
            if now - last_announce >= 3.0:
                try:
                    tx.sendto(payload, ("255.255.255.255", DISCOVERY_PORT))
                except OSError:
                    pass
                last_announce = now
                self.online = {
                    fp: p for fp, p in self.online.items()
                    if now - p["ts"] < 15.0
                }
            try:
                data, addr = rx.recvfrom(4096)
                info = json.loads(data.decode())
                if info.get("magic") != MAGIC:
                    continue
                fp = info.get("fp", "")
                if fp and fp != self.fingerprint:
                    self.online[fp] = {
                        "name": info.get("name", "?"),
                        "ip": addr[0],
                        "ts": time.time(),
                    }
            except (socket.timeout, ValueError, KeyError):
                continue
        rx.close()
        tx.close()

    def stop(self):
        self._stop.set()
