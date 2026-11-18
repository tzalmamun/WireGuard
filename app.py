#!/usr/bin/env python3
"""TZ WireGuard - a tiny, single-file WireGuard manager (admin panel + server).

Standard library only. Needs the `wg`, `ip`, `iptables` and `qrencode` tools
(installed by the Dockerfile). Creates WireGuard users and gives you their
config. Every user can optionally get a data limit (GB) and an expiry date;
with neither set the user is unlimited.
"""
import hashlib
import hmac
import html
import ipaddress
import json
import os
import re
import secrets
import shutil
import ssl
import subprocess
import threading
import time
import base64
import calendar
import datetime
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

DATA = os.environ.get("DATA_DIR", "/data")
DEFAULT_PASSWORD = "tzalmamun"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD") or DEFAULT_PASSWORD
WG_PORT = int(os.environ.get("WG_PORT", "51820"))
PANEL_PORT = int(os.environ.get("PANEL_LISTEN_PORT", "8080"))
SUBNET = ipaddress.ip_network(os.environ.get("WG_SUBNET", "10.8.0.0/20"))
DNS = os.environ.get("WG_DNS", "1.1.1.1, 8.8.8.8")
MTU = int(os.environ.get("WG_MTU", "1380"))
TZ_OFFSET = float(os.environ.get("TZ_OFFSET_HOURS", "6"))  # panel clock = UTC + this (Bangladesh = 6)
GB = 1024 ** 3
DRY = os.environ.get("TZ_DRY_RUN") == "1"  # tests only: skip system commands
TLS = os.environ.get("TLS", "1") == "1"
IFACE = "wg0"
NAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,32}$")
LOGO = "data:image/webp;base64,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"

STATE_PATH = os.path.join(DATA, "state.json")
lock = threading.RLock()
state = {"server_private": "", "server_public": "", "clients": {}}
_host_cache = {"v": ""}


# --------------------------------------------------------------- helpers ---
def log(*a):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), *a, flush=True)


def sh(args, input_text=None, check=True):
    if DRY:
        return ""
    p = subprocess.run(args, input=input_text, capture_output=True, text=True, timeout=20)
    if check and p.returncode != 0:
        raise RuntimeError("%s failed: %s" % (args[0], p.stderr.strip()))
    return p.stdout


def genkey():
    if DRY:
        return base64.b64encode(os.urandom(32)).decode()
    return sh(["wg", "genkey"]).strip()


def genpsk():
    if DRY:
        return base64.b64encode(os.urandom(32)).decode()
    return sh(["wg", "genpsk"]).strip()


def pubkey(priv):
    if DRY:
        return base64.b64encode(hashlib.sha256(priv.encode()).digest()).decode()
    return sh(["wg", "pubkey"], input_text=priv + "\n").strip()


def load_state():
    os.makedirs(DATA, mode=0o700, exist_ok=True)
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            state.update(json.load(f))


def save_state():
    tmp = STATE_PATH + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STATE_PATH)


def secret_key():
    p = os.path.join(DATA, "secret")
    if not os.path.exists(p):
        fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(secrets.token_hex(32))
    with open(p) as f:
        return f.read().strip().encode()


def server_host():
    h = os.environ.get("SERVER_HOST", "").strip()
    if h:
        return h
    if not _host_cache["v"]:
        try:
            with urllib.request.urlopen("https://api.ipify.org", timeout=8) as r:
                _host_cache["v"] = r.read().decode().strip()
        except Exception:
            _host_cache["v"] = "YOUR_SERVER_IP"
    return _host_cache["v"]


# ------------------------------------------------------------ wireguard ----
def default_iface():
    out = sh(["ip", "route", "show", "default"])
    m = re.search(r"dev (\S+)", out)
    return m.group(1) if m else "eth0"


def ipt(table, chain, rule):
    binary = shutil.which("iptables-legacy") or "iptables"
    check = [binary, "-t", table, "-C", chain] + rule
    if subprocess.run(check, capture_output=True).returncode != 0:
        sh([binary, "-t", table, "-A", chain] + rule)


def add_peer(c):
    sh(["wg", "set", IFACE, "peer", c["public"], "preshared-key", "/dev/stdin",
        "allowed-ips", c["ip"] + "/32"], input_text=c["psk"] + "\n")


def remove_peer(c):
    sh(["wg", "set", IFACE, "peer", c["public"], "remove"], check=False)
    _last.pop(c["public"], None)


def setup_wg():
    with lock:
        if not state["server_private"]:
            priv = genkey()
            state["server_private"] = priv
            state["server_public"] = pubkey(priv)
            save_state()
    if DRY:
        return
    sh(["ip", "link", "del", "dev", IFACE], check=False)
    sh(["ip", "link", "add", "dev", IFACE, "type", "wireguard"])
    sh(["wg", "set", IFACE, "listen-port", str(WG_PORT), "private-key", "/dev/stdin"],
       input_text=state["server_private"] + "\n")
    sh(["ip", "address", "add", "%s/%d" % (next(SUBNET.hosts()), SUBNET.prefixlen), "dev", IFACE])
    sh(["ip", "link", "set", "dev", IFACE, "mtu", str(MTU), "up"])
    out_if = default_iface()
    ipt("nat", "POSTROUTING", ["-s", str(SUBNET), "-o", out_if, "-j", "MASQUERADE"])
    ipt("filter", "FORWARD", ["-i", IFACE, "-j", "ACCEPT"])
    ipt("filter", "FORWARD", ["-o", IFACE, "-m", "state", "--state", "RELATED,ESTABLISHED", "-j", "ACCEPT"])
    with lock:
        for c in state["clients"].values():
            if c.get("enabled", True):
                add_peer(c)
    log("WireGuard up on UDP %d, %d users restored" % (WG_PORT, len(state["clients"])))


def next_ip():
    used = {c["ip"] for c in state["clients"].values()}
    server_ip = str(next(SUBNET.hosts()))
    for h in SUBNET.hosts():
        s = str(h)
        if s != server_ip and s not in used:
            return s
    raise RuntimeError("address pool is full")


REASON_TEXT = {"limit": "the data limit is reached", "expired": "the validity has expired"}


def parse_gb(text):
    text = (text or "").strip()
    if not text:
        return 0
    try:
        v = float(text)
    except ValueError:
        raise ValueError("Data limit must be a number of GB (e.g. 10 or 2.5). Leave empty for unlimited.")
    if v < 0 or v > 100000:
        raise ValueError("Data limit is out of range")
    return int(v * GB)


def parse_days(text):
    text = (text or "").strip()
    if not text:
        return 0
    if not text.isdigit() or int(text) > 3650:
        raise ValueError("Validity must be whole days (1-3650). Leave empty for no expiry.")
    d = int(text)
    return int(time.time()) + d * 86400 if d else 0


def parse_date(text):
    text = (text or "").strip()
    if not text:
        return 0
    try:
        dt = datetime.datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Expiry date must look like 2026-12-31. Leave empty for no expiry.")
    # valid until the end of that day, panel time
    return calendar.timegm(dt.replace(hour=23, minute=59, second=59).timetuple()) - int(TZ_OFFSET * 3600)


def used_bytes(c):
    return c.get("used_rx", 0) + c.get("used_tx", 0)


def over_reason(c):
    e = c.get("expire_at", 0)
    if e and time.time() >= e:
        return "expired"
    lim = c.get("limit_bytes", 0)
    if lim and used_bytes(c) >= lim:
        return "limit"
    return ""


def create_client(name, gb="", days=""):
    if not NAME_RE.match(name):
        raise ValueError("Name: 1-32 letters, digits, _ . -")
    limit = parse_gb(gb)
    expire = parse_days(days)
    with lock:
        if any(n.lower() == name.lower() for n in state["clients"]):
            raise ValueError("This name already exists")
        priv = genkey()
        c = {"private": priv, "public": pubkey(priv), "psk": genpsk(), "ip": next_ip(),
             "enabled": True, "created": int(time.time()),
             "limit_bytes": limit, "expire_at": expire, "used_rx": 0, "used_tx": 0, "reason": ""}
        add_peer(c)
        state["clients"][name] = c
        save_state()
    return c


def delete_client(name):
    with lock:
        c = state["clients"].pop(name, None)
        if c:
            remove_peer(c)
            save_state()


def disable_locked(c, reason=""):
    account_usage(peer_stats())
    remove_peer(c)
    c["enabled"] = False
    c["reason"] = reason


def enable_locked(c):
    add_peer(c)
    c["enabled"] = True
    c["reason"] = ""


def set_enabled(name, on):
    with lock:
        c = state["clients"].get(name)
        if not c:
            return
        if on and not c.get("enabled", True):
            r = over_reason(c)
            if r:
                raise ValueError("Cannot enable: %s. Raise the limit or extend the expiry first." % REASON_TEXT[r])
            enable_locked(c)
        elif not on and c.get("enabled", True):
            disable_locked(c, "")
        save_state()


def update_limits(name, gb, date):
    limit = parse_gb(gb)
    expire = parse_date(date)
    with lock:
        c = state["clients"].get(name)
        if not c:
            return
        c["limit_bytes"] = limit
        c["expire_at"] = expire
        r = over_reason(c)
        if c.get("enabled", True) and r:
            disable_locked(c, r)
        elif not c.get("enabled", True) and c.get("reason") in REASON_TEXT and not r:
            enable_locked(c)  # was stopped automatically, now allowed again
        save_state()


def reset_usage(name):
    with lock:
        c = state["clients"].get(name)
        if not c:
            return
        account_usage(peer_stats())  # move the counter baseline to "now"
        c["used_rx"] = 0
        c["used_tx"] = 0
        if not c.get("enabled", True) and c.get("reason") == "limit" and not over_reason(c):
            enable_locked(c)
        save_state()


def client_conf(name, c):
    return (
        "# TZ VPN - %s\n[Interface]\nPrivateKey = %s\nAddress = %s/32\nDNS = %s\nMTU = %d\n\n"
        "[Peer]\nPublicKey = %s\nPresharedKey = %s\nEndpoint = %s:%d\n"
        "AllowedIPs = 0.0.0.0/0, ::/0\nPersistentKeepalive = 25\n"
        % (name, c["private"], c["ip"], DNS, MTU, state["server_public"], c["psk"], server_host(), WG_PORT)
    )


def peer_stats():
    out = {}
    if DRY:
        return out
    try:
        for line in sh(["wg", "show", IFACE, "dump"]).splitlines()[1:]:
            f = line.split("\t")
            if len(f) >= 7:
                out[f[0]] = {"hs": int(f[4]), "rx": int(f[5]), "tx": int(f[6])}
    except Exception:
        pass
    return out


_last = {}  # public key -> (rx, tx) last counter values read from wg


def account_usage(stats):
    """Add the bytes moved since the last read to each user's saved total.
    wg counters restart from 0 when a peer is re-added or the container restarts,
    so only the difference is added. Call with `lock` held."""
    changed = False
    for c in state["clients"].values():
        st = stats.get(c["public"])
        if not st:
            continue
        lrx, ltx = _last.get(c["public"], (0, 0))
        drx = st["rx"] - lrx if st["rx"] >= lrx else st["rx"]
        dtx = st["tx"] - ltx if st["tx"] >= ltx else st["tx"]
        _last[c["public"]] = (st["rx"], st["tx"])
        if drx or dtx:
            c["used_rx"] = c.get("used_rx", 0) + drx
            c["used_tx"] = c.get("used_tx", 0) + dtx
            changed = True
    return changed


def enforce():
    stats = peer_stats()
    with lock:
        changed = account_usage(stats)
        for name, c in state["clients"].items():
            if c.get("enabled", True):
                r = over_reason(c)
                if r:
                    remove_peer(c)
                    c["enabled"] = False
                    c["reason"] = r
                    changed = True
                    log("user %s stopped: %s" % (name, REASON_TEXT[r]))
        if changed:
            save_state()


def monitor():
    while True:
        try:
            enforce()
        except Exception as e:
            log("monitor error:", e)
        time.sleep(20)


def qr_svg(text):
    if DRY:
        return b"<svg xmlns='http://www.w3.org/2000/svg' width='10' height='10'/>"
    p = subprocess.run(["qrencode", "-t", "SVG", "-o", "-", "-m", "2"], input=text.encode(),
                       capture_output=True, timeout=10)
    if p.returncode != 0:
        raise RuntimeError("qrencode failed")
    return p.stdout


# ------------------------------------------------------------- security ----
SECRET = b""
fails = {}  # ip -> [count, first_ts, blocked_until]
fails_lock = threading.Lock()


def blocked(ip):
    with fails_lock:
        f = fails.get(ip)
        return bool(f and time.time() < f[2])


def note_fail(ip):
    now = time.time()
    with fails_lock:
        f = fails.get(ip)
        if not f or now - f[1] > 600:
            f = [0, now, 0]
            fails[ip] = f
        f[0] += 1
        if f[0] >= 6:
            f[2] = now + 900


def sign(payload):
    return hmac.new(SECRET, payload.encode(), hashlib.sha256).hexdigest()


def make_session():
    payload = "%s.%d" % (secrets.token_hex(16), int(time.time()) + 12 * 3600)
    return payload + "." + sign(payload)


def session_id(tok):
    try:
        sid, exp, sig = tok.split(".")
    except ValueError:
        return None
    if not hmac.compare_digest(sig, sign("%s.%s" % (sid, exp))):
        return None
    if int(exp) < time.time():
        return None
    return sid


def csrf_for(sid):
    return sign("csrf:" + sid)


def check_password(given):
    a = hashlib.sha256(given.encode()).digest()
    b = hashlib.sha256(ADMIN_PASSWORD.encode()).digest()
    return hmac.compare_digest(a, b)


# ------------------------------------------------------------------ html ---
CSS = """
*{box-sizing:border-box}body{margin:0;font-family:system-ui,Segoe UI,Roboto,sans-serif;background:#f4f4f6;color:#222}
header{background:linear-gradient(135deg,#7a0f0f,#b3261e);color:#fff;padding:14px 16px;display:flex;align-items:center;gap:12px}
header img{width:42px;height:42px;border-radius:11px}header b{font-size:20px}header form{margin-left:auto}
main{max-width:760px;margin:auto;padding:12px}
.card{background:#fff;border-radius:16px;padding:14px;margin:12px 0;box-shadow:0 4px 16px #8b12121a}
input[type=text],input[type=password],input[type=date]{width:100%;font:inherit;padding:11px;border:1px solid #ccc;border-radius:10px;margin:4px 0}
button,.btn{display:inline-block;font:inherit;padding:10px 14px;border:0;border-radius:10px;background:#b3261e;color:#fff;cursor:pointer;text-decoration:none}
button.alt,.btn.alt{background:#555}button.danger{background:#7a0f0f}
.row{display:flex;gap:8px;flex-wrap:wrap}.row>*{flex:1;min-width:120px;text-align:center}
.tag{display:inline-block;padding:2px 9px;border-radius:10px;font-size:12px;background:#ddd}
.on{background:#c8f0d0}.off{background:#f6d0d0}small,.muted{color:#777}
pre{background:#111;color:#e8e8e8;padding:12px;border-radius:10px;overflow:auto;font-size:12px;white-space:pre-wrap;word-break:break-all}
table{width:100%;border-collapse:collapse;font-size:14px}td{padding:5px 0;vertical-align:top;word-break:break-all}td:first-child{color:#777;width:38%}
.err{color:#b3261e;margin:6px 0}label{display:block;margin-top:8px;color:#777;font-size:14px}a.item{color:inherit;text-decoration:none;display:block}
"""


def esc(s):
    return html.escape(str(s), quote=True)


def page(title, body, csrf=None):
    head = "<header><img src='%s' alt=''><b>TZ VPN</b>" % LOGO
    if csrf:
        head += "<form method='post' action='/logout'><input type='hidden' name='csrf' value='%s'><button class='alt'>Logout</button></form>" % esc(csrf)
    head += "</header>"
    return ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<meta name='color-scheme' content='light'><link rel='icon' href='%s'>"
            "<title>%s</title><style>%s</style></head><body>%s<main>%s</main></body></html>"
            % (LOGO, esc(title), CSS, head, body)).encode()


def fmt_bytes(n):
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or u == "TB":
            return ("%d %s" % (n, u)) if u == "B" else ("%.2f %s" % (n, u))
        n /= 1024.0


def fmt_time(ts):
    return time.strftime("%Y-%m-%d %H:%M", time.gmtime(ts + TZ_OFFSET * 3600))


def fmt_expiry(c):
    e = c.get("expire_at", 0)
    if not e:
        return "never"
    left = e - time.time()
    if left <= 0:
        return fmt_time(e) + " (expired)"
    if left < 86400:
        return fmt_time(e) + " (less than a day left)"
    return "%s (%d days left)" % (fmt_time(e), left // 86400)


def fmt_data(c):
    lim = c.get("limit_bytes", 0)
    return "%s / %s" % (fmt_bytes(used_bytes(c)), fmt_bytes(lim) if lim else "unlimited")


def status_of(c, st):
    if not c.get("enabled", True):
        return {"limit": "limit reached", "expired": "expired"}.get(c.get("reason"), "disabled"), "off"
    hs = st.get("hs", 0)
    if hs and time.time() - hs < 180:
        return "online", "on"
    return "offline", ""


# --------------------------------------------------------------- server ----
class H(BaseHTTPRequestHandler):
    server_version = "TZ"
    timeout = 20

    def log_message(self, *a):
        pass

    def ip(self):
        return self.client_address[0]

    def send(self, code, body=b"", ctype="text/html; charset=utf-8", headers=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy",
                         "default-src 'none'; img-src 'self' data:; style-src 'unsafe-inline'; "
                         "script-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def redirect(self, to, headers=None):
        self.send(303, b"", headers=dict({"Location": to}, **(headers or {})))

    def session(self):
        for part in self.headers.get("Cookie", "").split(";"):
            k, _, v = part.strip().partition("=")
            if k == "tzsess":
                return session_id(v)
        return None

    def form(self):
        n = int(self.headers.get("Content-Length", "0") or 0)
        if n > 8192:
            return {}
        return {k: v[0] for k, v in parse_qs(self.rfile.read(n).decode("utf-8", "replace")).items()}

    # ---- routing
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/login":
            return self.login_page()
        sid = self.session()
        if not sid:
            return self.redirect("/login")
        if path == "/":
            return self.dashboard(sid)
        m = re.match(r"^/u/([A-Za-z0-9_.-]{1,32})(/config|/qr\.svg)?$", path)
        if m:
            return self.user_page(sid, m.group(1), m.group(2))
        self.send(404, page("Not found", "<div class='card'>Not found</div>"))

    def do_POST(self):
        path = urlparse(self.path).path
        f = self.form()
        if path == "/login":
            return self.do_login(f)
        sid = self.session()
        if not sid or not hmac.compare_digest(f.get("csrf", ""), csrf_for(sid)):
            return self.redirect("/login")
        if path == "/logout":
            return self.redirect("/login", {"Set-Cookie": self.cookie("", 0)})
        if path == "/create":
            try:
                name = f.get("name", "").strip()
                create_client(name, f.get("gb", ""), f.get("days", ""))
                return self.redirect("/u/" + name)
            except Exception as e:
                return self.dashboard(sid, str(e))
        m = re.match(r"^/u/([A-Za-z0-9_.-]{1,32})/(toggle|delete|update|reset)$", path)
        if m:
            name, action = m.groups()
            if name in state["clients"]:
                if action == "delete":
                    delete_client(name)
                    return self.redirect("/")
                try:
                    if action == "toggle":
                        set_enabled(name, not state["clients"][name].get("enabled", True))
                    elif action == "update":
                        update_limits(name, f.get("gb", ""), f.get("date", ""))
                    else:
                        reset_usage(name)
                except Exception as e:
                    return self.user_page(sid, name, None, str(e))
            return self.redirect("/u/" + name)
        self.send(404, page("Not found", "<div class='card'>Not found</div>"))

    def cookie(self, value, age):
        return "tzsess=%s; HttpOnly; SameSite=Strict; Path=/; Max-Age=%d%s" % (value, age, "; Secure" if TLS else "")

    # ---- pages
    def login_page(self, err=""):
        body = ("<div class='card'><h2>Admin login</h2><form method='post' action='/login'>"
                "<input type='password' name='password' placeholder='Admin password' autofocus>"
                "<div class='err'>%s</div><button style='width:100%%'>Login</button></form></div>" % esc(err))
        self.send(200, page("Login", body))

    def do_login(self, f):
        ip = self.ip()
        if blocked(ip):
            return self.send(429, page("Blocked", "<div class='card'>Too many attempts. Try again in 15 minutes.</div>"))
        if check_password(f.get("password", "")):
            return self.redirect("/", {"Set-Cookie": self.cookie(make_session(), 12 * 3600)})
        note_fail(ip)
        time.sleep(1)
        self.login_page("Wrong password")

    def dashboard(self, sid, err=""):
        csrf = csrf_for(sid)
        stats = peer_stats()
        with lock:
            items = sorted(state["clients"].items(), key=lambda kv: -kv[1].get("created", 0))
            cards = ""
            for name, c in items:
                st = stats.get(c["public"], {})
                label, cls = status_of(c, st)
                cards += ("<div class='card'><a class='item' href='/u/%s'><b>%s</b> <span class='tag %s'>%s</span>"
                          "<div class='muted'>%s &middot; down %s &middot; up %s</div>"
                          "<div class='muted'>Data %s &middot; Expires %s</div></a></div>"
                          % (esc(name), esc(name), cls, label, esc(c["ip"]),
                             fmt_bytes(c.get("used_tx", 0)), fmt_bytes(c.get("used_rx", 0)),
                             esc(fmt_data(c)), esc(fmt_expiry(c))))
            total = len(items)
        warn = ""
        if ADMIN_PASSWORD == DEFAULT_PASSWORD:
            warn = ("<div class='card' style='border:2px solid #b3261e'><b style='color:#b3261e'>Default admin password in use.</b> "
                    "Change it: edit <code>ADMIN_PASSWORD</code> in <code>/opt/tz-wg/.env</code>, then run "
                    "<code>docker compose up -d</code> in that folder.</div>")
        body = (warn + "<div class='card'><b>Create new user</b><form method='post' action='/create'>"
                "<input type='hidden' name='csrf' value='%s'><input type='text' name='name' placeholder='User name (e.g. rahim)' maxlength='32'>"
                "<div class='row'><input type='text' name='gb' inputmode='decimal' placeholder='Data limit in GB (empty = unlimited)'>"
                "<input type='text' name='days' inputmode='numeric' placeholder='Valid for days (empty = no expiry)'></div>"
                "<div class='err'>%s</div><button style='width:100%%'>Create</button></form></div>"
                "<h3>Users (%d)</h3>%s"
                % (esc(csrf), esc(err), total, cards or "<div class='card muted'>No users yet.</div>"))
        self.send(200, page("TZ VPN", body, csrf))

    def user_page(self, sid, name, sub, err=""):
        with lock:
            c = state["clients"].get(name)
            if not c:
                return self.send(404, page("Not found", "<div class='card'>User not found</div>"))
            conf = client_conf(name, c)
            c = dict(c)
        if sub == "/config":
            return self.send(200, conf.encode(), "application/octet-stream",
                             {"Content-Disposition": 'attachment; filename="tz-%s.conf"' % name})
        if sub == "/qr.svg":
            try:
                return self.send(200, qr_svg(conf), "image/svg+xml")
            except Exception:
                return self.send(500, b"QR unavailable", "text/plain")
        csrf = csrf_for(sid)
        enabled = c.get("enabled", True)
        st = peer_stats().get(c["public"], {})
        label, cls = status_of(c, st)
        hs = st.get("hs", 0)
        last = fmt_time(hs) if hs else "never"
        lim = c.get("limit_bytes", 0)
        gb_val = ("%g" % (lim / float(GB))) if lim else ""
        e = c.get("expire_at", 0)
        date_val = time.strftime("%Y-%m-%d", time.gmtime(e + TZ_OFFSET * 3600)) if e else ""

        def post(action, text, kind=""):
            confirm = " onclick=\"return confirm('Delete this user?')\"" if action == "delete" else ""
            return ("<form method='post' action='/u/%s/%s' style='flex:1'><input type='hidden' name='csrf' value='%s'>"
                    "<button class='%s' style='width:100%%'%s>%s</button></form>" % (esc(name), action, esc(csrf), kind, confirm, text))

        rows = [("Status", "<span class='tag %s'>%s</span>" % (cls, label)), ("Last handshake", esc(last)),
                ("Data used", esc(fmt_data(c))), ("Downloaded", fmt_bytes(c.get("used_tx", 0))),
                ("Uploaded", fmt_bytes(c.get("used_rx", 0))), ("Expires", esc(fmt_expiry(c))),
                ("Address", esc(c["ip"] + "/32")), ("DNS", esc(DNS)), ("MTU", str(MTU)),
                ("Endpoint", esc("%s:%d" % (server_host(), WG_PORT))), ("Server public key", esc(state["server_public"])),
                ("Client public key", esc(c["public"])), ("Allowed IPs", "0.0.0.0/0, ::/0")]
        table = "".join("<tr><td>%s</td><td>%s</td></tr>" % r for r in rows)
        limits = ("<div class='card'><b>Limits</b> <small>(empty = no limit)</small>"
                  "<form method='post' action='/u/%s/update'><input type='hidden' name='csrf' value='%s'>"
                  "<label>Data limit (GB)</label><input type='text' name='gb' inputmode='decimal' value='%s' placeholder='unlimited'>"
                  "<label>Valid until (date)</label><input type='date' name='date' value='%s'>"
                  "<button style='width:100%%;margin-top:10px'>Save limits</button></form>"
                  "<div style='margin-top:8px'>%s</div></div>"
                  % (esc(name), esc(csrf), esc(gb_val), esc(date_val), post("reset", "Reset used data to 0", "alt")))
        body = ("<p><a href='/'>&larr; All users</a></p>"
                "<div class='card'><h2 style='margin-top:0'>%s</h2><div class='err'>%s</div><table>%s</table></div>"
                "%s"
                "<div class='card'><b>Config</b> <small>(import this in your WireGuard / VPN app)</small>"
                "<div class='row' style='margin:8px 0'><a class='btn' href='/u/%s/config'>Download .conf</a>"
                "<button class='alt' type='button' onclick=\"navigator.clipboard.writeText(document.getElementById('c').innerText).then(()=>this.innerText='Copied')\">Copy</button></div>"
                "<pre id='c'>%s</pre><div style='text-align:center;background:#fff'><img src='/u/%s/qr.svg' alt='QR' style='width:260px;max-width:100%%'></div></div>"
                "<div class='row'>%s%s</div>"
                % (esc(name), esc(err), table, limits, esc(name), esc(conf), esc(name),
                   post("toggle", "Disable" if enabled else "Enable", "alt"), post("delete", "Delete", "danger")))
        self.send(200, page(name, body, csrf))


class Srv(ThreadingHTTPServer):
    daemon_threads = True
    ctx = None

    def get_request(self):
        sock, addr = self.socket.accept()
        sock.settimeout(20)
        if self.ctx:
            sock = self.ctx.wrap_socket(sock, server_side=True, do_handshake_on_connect=False)
        return sock, addr

    def handle_error(self, request, client_address):
        pass


def ensure_cert():
    crt, key = os.path.join(DATA, "tls.crt"), os.path.join(DATA, "tls.key")
    if not (os.path.exists(crt) and os.path.exists(key)):
        subprocess.run(["openssl", "req", "-x509", "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:prime256v1",
                        "-nodes", "-days", "3650", "-subj", "/CN=TZ-WG", "-keyout", key, "-out", crt],
                       check=True, capture_output=True)
        os.chmod(key, 0o600)
    return crt, key


def main():
    global SECRET
    if len(ADMIN_PASSWORD) < 8:
        raise SystemExit("ADMIN_PASSWORD must be set (at least 8 characters)")
    load_state()
    SECRET = secret_key()
    setup_wg()
    threading.Thread(target=monitor, daemon=True).start()
    srv = Srv(("0.0.0.0", PANEL_PORT), H)
    if TLS:
        crt, key = ensure_cert()
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.load_cert_chain(crt, key)
        srv.ctx = ctx
    log("TZ WireGuard panel on %s port %d" % ("https" if TLS else "http", PANEL_PORT))
    srv.serve_forever()


if __name__ == "__main__":
    main()
