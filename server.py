# -*- coding: utf-8 -*-
"""
SENTIA bridge — server locale che espone i parametri reali del PC alla
dashboard organica. Focus gamer: CPU, RAM, disco, rete (throughput + ping,
jitter, perdita pacchetti), GPU e temperatura CPU quando disponibili.
Dipendenza: psutil (installata automaticamente al primo avvio).
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 7107
# quando gira come .exe (PyInstaller) i file dati sono dentro sys._MEIPASS
BASE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
STATIC_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".ico": "image/x-icon",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
}
NO_WINDOW = 0x08000000  # CREATE_NO_WINDOW: niente flash di console sotto pythonw


def ensure_psutil():
    try:
        import psutil  # noqa: F401
        return
    except ImportError:
        print("[SENTIA] installo psutil...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "psutil"])


ensure_psutil()
import psutil  # noqa: E402

psutil.cpu_percent(interval=None)  # priming: la prima lettura e' sempre 0.0
_last_net = psutil.net_io_counters()
_last_dio = psutil.disk_io_counters()
_last_t = time.time()


def top_procs():
    cpu_l, mem_l = [], []
    for p in psutil.process_iter(["name", "cpu_percent", "memory_percent"]):
        try:
            cpu_l.append((p.info["cpu_percent"] or 0.0, p.info["name"] or "?"))
            mem_l.append((p.info["memory_percent"] or 0.0, p.info["name"] or "?"))
        except Exception:
            pass
    top_cpu = sorted(cpu_l, reverse=True)[:6]
    top_mem = sorted(mem_l, reverse=True)[:6]
    return ([{"name": n, "val": round(v, 1)} for v, n in top_cpu],
            [{"name": n, "val": round(v, 1)} for v, n in top_mem])

# ---------- GPU via nvidia-smi (se presente) ----------
_NV = shutil.which("nvidia-smi")


def gpu_info():
    if not _NV:
        return None
    try:
        out = subprocess.run(
            [_NV, "--query-gpu=temperature.gpu,utilization.gpu,memory.used,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=2, creationflags=NO_WINDOW)
        t, util, mused, mtot = [x.strip() for x in out.stdout.splitlines()[0].split(",")]
        return {"temp": float(t), "util": float(util),
                "mem_used": float(mused), "mem_total": float(mtot)}
    except Exception:
        return None


# ---------- Temperatura CPU: psutil (Linux) o WMI (Windows), con cache ----------
_temp_cache = [0.0, None]


def cpu_temp():
    now = time.time()
    if now - _temp_cache[0] < 6:
        return _temp_cache[1]
    val = None
    try:
        temps = psutil.sensors_temperatures()
        for entries in temps.values():
            if entries:
                val = max(e.current for e in entries)
                break
    except Exception:
        pass
    if val is None and os.name == "nt":
        try:
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-CimInstance -Namespace root/wmi -Class "
                 "MSAcpi_ThermalZoneTemperature -ErrorAction Stop | "
                 "Select-Object -First 1).CurrentTemperature"],
                capture_output=True, text=True, timeout=4, creationflags=NO_WINDOW)
            raw = out.stdout.strip()
            if raw:
                val = round(float(raw) / 10.0 - 273.15, 1)
                if not (0 < val < 130):
                    val = None
        except Exception:
            val = None
    _temp_cache[0], _temp_cache[1] = now, val
    return val


# ---------- Qualita' internet: RTT TCP, jitter, perdita (cache 5s) ----------
_net_cache = [0.0, {"ping_ms": None, "jitter_ms": None, "loss_pct": None}]


def _tcp_rtt(host, port=443, timeout=1.2):
    t = time.perf_counter()
    try:
        s = socket.create_connection((host, port), timeout)
        s.close()
        return (time.perf_counter() - t) * 1000.0
    except OSError:
        return None


def net_quality():
    now = time.time()
    if now - _net_cache[0] < 5:
        return _net_cache[1]
    samples = []
    fails = 0
    for host in ("1.1.1.1", "8.8.8.8"):
        for _ in range(3):
            r = _tcp_rtt(host)
            if r is None:
                fails += 1
            else:
                samples.append(r)
    if samples:
        ping = round(min(samples), 1)
        avg = sum(samples) / len(samples)
        jitter = round(sum(abs(s - avg) for s in samples) / len(samples), 1)
    else:
        ping = jitter = None
    loss = round(fails / 6.0 * 100.0, 1)
    _net_cache[0] = now
    _net_cache[1] = {"ping_ms": ping, "jitter_ms": jitter, "loss_pct": loss}
    return _net_cache[1]


def collect():
    global _last_net, _last_dio, _last_t
    now = time.time()
    dt = max(now - _last_t, 0.1)

    net = psutil.net_io_counters()
    down = (net.bytes_recv - _last_net.bytes_recv) / dt
    up = (net.bytes_sent - _last_net.bytes_sent) / dt
    _last_net = net

    dio = psutil.disk_io_counters()
    d_read = (dio.read_bytes - _last_dio.read_bytes) / dt
    d_write = (dio.write_bytes - _last_dio.write_bytes) / dt
    _last_dio = dio
    _last_t = now

    batt = psutil.sensors_battery()
    disk = psutil.disk_usage(os.path.abspath(os.sep))
    top_cpu, top_mem = top_procs()
    try:
        conns = len(psutil.net_connections(kind="tcp"))
    except Exception:
        conns = None

    data = {
        "cpu": psutil.cpu_percent(interval=None),
        "cores": psutil.cpu_percent(percpu=True),
        "cpu_temp": cpu_temp(),
        "gpu": gpu_info(),
        "ram": psutil.virtual_memory().percent,
        "disk": disk.percent,
        "mount": os.path.abspath(os.sep),
        "net_down": down,
        "net_up": up,
        "disk_r": d_read,
        "disk_w": d_write,
        "conns": conns,
        "top_cpu": top_cpu,
        "top_mem": top_mem,
        "batt": batt.percent if batt else None,
        "batt_ch": batt.power_plugged if batt else None,
        "procs": len(psutil.pids()),
        "uptime": now - psutil.boot_time(),
    }
    data.update(net_quality())
    return data


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # silenzioso

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        try:
            if path == "/metrics":
                self._send(200, json.dumps(collect()).encode(), "application/json")
                return
            name = os.path.basename(path) or "sentia.html"
            if name in ("index.html",):
                name = "sentia.html"
            ext = os.path.splitext(name)[1].lower()
            ctype = STATIC_TYPES.get(ext)
            fp = os.path.join(BASE, name)
            if ctype and os.path.isfile(fp):
                with open(fp, "rb") as f:
                    self._send(200, f.read(), ctype)
            else:
                self._send(404, b"not found", "text/plain")
        except Exception as exc:  # mai far cadere il ponte
            try:
                self._send(500, str(exc).encode(), "text/plain")
            except Exception:
                pass


if __name__ == "__main__":
    import webbrowser

    try:
        srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        # ponte gia' attivo: apri solo la pagina
        webbrowser.open(f"http://localhost:{PORT}/")
        sys.exit(0)

    def _open():
        time.sleep(1.0)
        try:
            webbrowser.open(f"http://localhost:{PORT}/")
        except Exception:
            pass

    threading.Thread(target=_open, daemon=True).start()
    print(f"[SENTIA] ponte attivo su http://localhost:{PORT}/  (Ctrl+C per chiudere)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
