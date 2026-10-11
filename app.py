"""AIOS Workspace: a standalone Streamlit front end for the AIOS backend.

Run it from the project root (next to alembic.ini and app/):

    uv run streamlit run streamlit_app.py

Place this file in the project root (next to docker-compose.yml, alembic.ini and app/).

On start it will:
  1. start the Docker services (`docker compose up -d postgres redis qdrant`) and wait
     until they accept connections,
  2. apply database migrations (`alembic upgrade head`, retried while the DB warms up),
  3. start the FastAPI backend (uvicorn) as a managed subprocess,
  4. wait for the health check, then open the workspace.

Your .env must point at the host-published ports (e.g. localhost), not at compose-internal
hostnames such as `postgres`, because the API runs on the host.

Environment variables
  AIOS_API_URL          Use an API managed elsewhere (e.g. http://host:8000/api/v1). Docker,
                        migrations and the local API are all skipped in this mode.
  AIOS_API_PORT         Preferred local port for the managed API (default 8000).
  AIOS_DOCKER_SERVICES  Compose services to start (default "postgres redis qdrant").
  AIOS_SKIP_DOCKER      Set to 1 if you run the services yourself.
  AIOS_STOP_DOCKER      Set to 1 to stop the containers when this app exits.

Endpoint paths and request fields are discovered from the running API's /openapi.json,
so the UI adapts to the real route and schema names. Requires streamlit >= 1.40 and requests.
"""
from __future__ import annotations

import atexit
import html
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
import streamlit as st

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
API_PREFIX = "/api/v1"
EXTERNAL_API = os.getenv("AIOS_API_URL", "").strip().rstrip("/")
if EXTERNAL_API and not EXTERNAL_API.endswith(API_PREFIX):
    EXTERNAL_API += API_PREFIX
PREFERRED_PORT = int(os.getenv("AIOS_API_PORT", "8000"))
LOG_FILE = Path(tempfile.gettempdir()) / "aios_api.log"
KB_BASES = ("/knowledge-bases", "/knowledge_bases", "/knowledgebases")
DOCKER_SERVICES = tuple(os.getenv("AIOS_DOCKER_SERVICES", "postgres redis qdrant").split())
SKIP_DOCKER = os.getenv("AIOS_SKIP_DOCKER", "").lower() in ("1", "true", "yes")
STOP_DOCKER = os.getenv("AIOS_STOP_DOCKER", "").lower() in ("1", "true", "yes")
COMPOSE_FILES = ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml")
SERVICE_PORTS = {"postgres": 5432, "redis": 6379, "qdrant": 6333}

st.set_page_config(
    page_title="AIOS",
    page_icon=":material/hub:",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _ensure_theme() -> None:
    """Write a light theme config on first run so native widgets match the design."""
    cfg = ROOT / ".streamlit" / "config.toml"
    if cfg.exists():
        return
    try:
        cfg.parent.mkdir(exist_ok=True)
        cfg.write_text(
            '[theme]\nbase = "light"\nprimaryColor = "#1F5F5B"\nbackgroundColor = "#F3F5F4"\n'
            'secondaryBackgroundColor = "#E8EEEC"\ntextColor = "#17252A"\nfont = "sans serif"\n',
            encoding="utf-8",
        )
    except OSError:
        pass


_ensure_theme()

# ----------------------------------------------------------------------------
# Design system
# ----------------------------------------------------------------------------
CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&display=swap');
:root{
  --paper:#F3F5F4; --surface:#FFFFFF; --pine:#10292B; --pine-2:#1B3D40; --brand:#1F5F5B;
  --brand-ink:#0F3F3C; --amber:#B8730F; --amber-bg:#FBF3E4; --text:#17252A; --muted:#5E6F73;
  --line:#DDE4E2; --danger:#B42318; --ok:#1E7B4E; --serif:'Newsreader', Georgia, serif;
}
.stApp, .stApp p, .stApp label, .stApp li, .stApp input, .stApp textarea, .stApp button,
.stApp h1, .stApp h2, .stApp h3, .stApp h4 { font-family:'Instrument Sans', system-ui, sans-serif; }
.stApp{ background:var(--paper); color:var(--text); }
.block-container{ padding-top:2.2rem; padding-bottom:5rem; max-width:1200px; }
header[data-testid="stHeader"]{ background:transparent; }
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"]{ visibility:hidden; height:0; }
h1,h2,h3{ letter-spacing:-0.01em; font-weight:650; color:var(--text); }
.page-title{ font-size:1.8rem; font-weight:650; letter-spacing:-0.015em; line-height:1.2; margin-bottom:.25rem; }
.page-sub{ color:var(--muted); font-size:.98rem; margin-bottom:1.4rem; max-width:62ch; }
.muted{ color:var(--muted); font-size:.86rem; }
.section-title{ font-size:1.02rem; font-weight:600; margin:.4rem 0 .6rem; }

/* sidebar */
section[data-testid="stSidebar"]{ background:var(--pine); border-right:none; }
section[data-testid="stSidebar"] *{ color:#D3E2DF; }
[data-testid="stSidebarNav"]::before{ content:"AIOS"; display:block; font-weight:700; font-size:1.4rem;
  letter-spacing:.03em; color:#fff; padding:1.2rem 1rem .6rem; }
[data-testid="stSidebarNavLink"]{ border-radius:8px; margin:1px 8px; }
[data-testid="stSidebarNavLink"]:hover{ background:rgba(255,255,255,.07); }
[data-testid="stSidebarNavLink"][aria-current="page"]{ background:rgba(255,255,255,.13); }
[data-testid="stSidebarNavLink"][aria-current="page"] span{ color:#fff; font-weight:600; }
section[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]{
  background:transparent; border:1px solid rgba(255,255,255,.22); }
section[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover{ background:rgba(255,255,255,.08); }
.userchip{ display:flex; gap:.7rem; align-items:center; padding:.8rem .6rem; border-top:1px solid rgba(255,255,255,.12); margin-top:1rem; }
.userchip .av{ width:34px; height:34px; border-radius:50%; background:var(--brand); color:#fff !important; display:flex;
  align-items:center; justify-content:center; font-weight:600; font-size:.85rem; flex:none; }
.userchip .who{ line-height:1.25; overflow:hidden; }
.userchip .who b{ color:#fff; font-weight:600; font-size:.9rem; display:block; white-space:nowrap; text-overflow:ellipsis; overflow:hidden; }
.userchip .who span{ font-size:.78rem; opacity:.8; display:block; white-space:nowrap; text-overflow:ellipsis; overflow:hidden; }

/* buttons */
[data-testid="stBaseButton-primary"], button[kind="primary"], [data-testid="stBaseButton-primaryFormSubmit"]{
  background:var(--brand); border:1px solid var(--brand); color:#fff; border-radius:8px; font-weight:600; }
[data-testid="stBaseButton-primary"]:hover, [data-testid="stBaseButton-primaryFormSubmit"]:hover{ background:var(--brand-ink); border-color:var(--brand-ink); color:#fff; }
[data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-secondaryFormSubmit"]{
  background:var(--surface); border:1px solid var(--line); border-radius:8px; color:var(--text); font-weight:500; }
[data-testid="stBaseButton-secondary"]:hover{ border-color:var(--brand); color:var(--brand); }
button:focus-visible{ outline:2px solid var(--brand); outline-offset:2px; }

/* inputs */
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div{
  background:#fff; border-radius:8px; border-color:var(--line); }
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within, [data-baseweb="select"] > div:focus-within{
  border-color:var(--brand); box-shadow:0 0 0 3px rgba(31,95,91,.16); }
[data-testid="stFileUploaderDropzone"]{ background:#fff; border:1.5px dashed #B9C8C5; border-radius:12px; }
[data-testid="stForm"]{ background:var(--surface); border:1px solid var(--line); border-radius:12px; padding:1.1rem 1.2rem; }
[data-testid="stVerticalBlockBorderWrapper"]{ border-color:var(--line); border-radius:12px; background:var(--surface); }
[data-testid="stExpander"]{ background:var(--surface); border:1px solid var(--line); border-radius:12px; }
button[role="tab"]{ font-weight:500; }
button[role="tab"][aria-selected="true"]{ color:var(--brand); }
[data-baseweb="tab-highlight"]{ background:var(--brand); }

/* chat */
[data-testid="stChatMessage"]{ background:transparent; padding:.7rem .2rem; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]){
  background:#E6EDEB; border-radius:12px; padding:.8rem 1rem; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stMarkdownContainer"] p,
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stMarkdownContainer"] li{
  font-family:var(--serif); font-size:1.08rem; line-height:1.7; }
[data-testid="stChatInput"]{ border-radius:14px; border-color:var(--line); }

/* sources, status */
.passage{ background:var(--surface); border:1px solid var(--line); border-left:4px solid var(--amber);
  border-radius:4px 12px 12px 4px; padding:.8rem 1rem; margin:0 0 .7rem; }
.passage-head{ display:flex; gap:.8rem; align-items:center; margin-bottom:.45rem; font-size:.88rem; flex-wrap:wrap; }
.passage-text{ font-family:var(--serif); font-size:1.02rem; line-height:1.65; max-height:11rem; overflow:auto; color:#26373B; }
.meter{ margin-left:auto; width:84px; height:6px; background:#EDE3CF; border-radius:3px; overflow:hidden; display:inline-block; }
.meter i{ display:block; height:100%; background:var(--amber); }
.badge{ display:inline-block; padding:.12rem .55rem; border-radius:999px; font-size:.78rem; font-weight:600; }
.badge.ok{ background:#E2F3EA; color:var(--ok); } .badge.warn{ background:var(--amber-bg); color:var(--amber); }
.badge.bad{ background:#FCE8E6; color:var(--danger); } .badge.neutral{ background:#E6EDEB; color:var(--muted); }
.answer{ font-family:var(--serif); font-size:1.12rem; line-height:1.75; background:var(--surface);
  border:1px solid var(--line); border-radius:12px; padding:1.1rem 1.3rem; margin-bottom:1rem; }
.empty{ text-align:center; padding:3rem 1rem; color:var(--muted); }
.empty h3{ color:var(--text); margin-bottom:.3rem; }
.agent-desc{ color:var(--muted); font-size:.92rem; min-height:2.6rem; }

/* auth */
.auth-panel{ background:var(--pine); border-radius:18px; padding:2.8rem 2.4rem; min-height:36rem; color:#fff; }
.auth-panel .mark{ font-weight:700; font-size:1.3rem; letter-spacing:.03em; margin-bottom:3rem; }
.auth-panel h1{ font-family:var(--serif); color:#fff; font-size:2.5rem; line-height:1.15; font-weight:500; margin:0 0 1rem; }
.auth-panel p{ color:#B9CFCB; max-width:36ch; line-height:1.6; }
.auth-demo{ margin-top:2.2rem; background:rgba(255,255,255,.06); border-radius:12px; padding:1rem 1.1rem; }
.auth-demo .q{ font-size:.86rem; color:#9FBBB6; margin-bottom:.4rem; }
.auth-demo .a{ font-family:var(--serif); font-size:1.05rem; line-height:1.55; color:#fff; }
.auth-demo .src{ margin-top:.7rem; border-left:3px solid #E0A23A; padding-left:.7rem; font-size:.84rem; color:#D9C9A5; }
@media (prefers-reduced-motion: reduce){ *{ transition:none !important; animation:none !important; } }
"""

st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Backend lifecycle: migrate, start API, wait for health
# ----------------------------------------------------------------------------
@dataclass
class Backend:
    ok: bool
    base: str
    mode: str
    migration_log: str = ""
    error: str = ""
    port: int | None = None


def _port_open(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _healthy(base: str, timeout: float = 2.0) -> bool:
    try:
        return requests.get(f"{base}/health/health", timeout=timeout).ok
    except requests.RequestException:
        return False


def _stop(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def _log_tail(lines: int = 40) -> str:
    try:
        return "\n".join(LOG_FILE.read_text(errors="replace").splitlines()[-lines:])
    except OSError:
        return ""


def _compose(*args: str, timeout: int = 600) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", "compose", *args], cwd=ROOT, capture_output=True, text=True, timeout=timeout)


def _wait_for_service(svc: str, deadline: float) -> str | None:
    """Return an error message if the service is not ready before the deadline."""
    if svc == "postgres":
        while time.time() < deadline:
            try:
                if _compose("exec", "-T", svc, "pg_isready", timeout=15).returncode == 0:
                    return None
            except (OSError, subprocess.TimeoutExpired):
                pass
            time.sleep(1.5)
        return "PostgreSQL did not become ready in time."
    internal = SERVICE_PORTS.get(svc)
    if not internal:
        return None
    try:
        out = _compose("port", svc, str(internal), timeout=20).stdout.strip().splitlines()
    except (OSError, subprocess.TimeoutExpired):
        return None
    if not out or ":" not in out[0]:
        return None  # port not published to the host; nothing to wait on
    host_port = int(out[0].rsplit(":", 1)[1])
    while time.time() < deadline:
        if _port_open(host_port):
            return None
        time.sleep(1)
    return f"{svc} did not accept connections on port {host_port} in time."


_docker_stop_registered = False


def start_docker_services() -> tuple[bool, str]:
    """Start the compose services this app depends on. Returns (ok, log)."""
    global _docker_stop_registered
    if SKIP_DOCKER or not DOCKER_SERVICES:
        return True, "Docker step skipped (AIOS_SKIP_DOCKER)."
    if not any((ROOT / f).exists() for f in COMPOSE_FILES):
        return True, "No compose file found in the project root; assuming services are already running."
    if shutil.which("docker") is None:
        return True, "Docker is not installed; assuming services are already running."
    try:
        up = _compose("up", "-d", *DOCKER_SERVICES)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"Could not run docker compose: {exc}"
    log = f"{up.stdout}\n{up.stderr}".strip()
    if up.returncode != 0:
        return False, f"{log}\n\nDocker could not start the services. Make sure Docker Desktop (or the Docker daemon) is running."
    deadline = time.time() + 120
    for svc in DOCKER_SERVICES:
        err = _wait_for_service(svc, deadline)
        if err:
            return False, f"{log}\n\n{err}"
    if STOP_DOCKER and not _docker_stop_registered:
        atexit.register(lambda: _compose("stop", *DOCKER_SERVICES, timeout=120))
        _docker_stop_registered = True
    return True, f"{log}\n\nDocker services ready: {', '.join(DOCKER_SERVICES)}."


@st.cache_resource(show_spinner="Starting services, applying migrations and launching the API…")
def boot_backend() -> Backend:
    note = ""
    if EXTERNAL_API:
        if _healthy(EXTERNAL_API, 5):
            return Backend(True, EXTERNAL_API, "external")
        note = f"AIOS_API_URL ({EXTERNAL_API}) was not reachable, so the API was started locally instead.\n\n"

    docker_ok, docker_log = start_docker_services()
    docker_log = note + docker_log
    if not docker_ok:
        return Backend(False, "", "managed", docker_log, "The Docker services could not be started.")

    mig = None
    for attempt in range(5):  # the database may still be warming up right after start
        try:
            mig = subprocess.run(
                [sys.executable, "-m", "alembic", "upgrade", "head"],
                cwd=ROOT, capture_output=True, text=True, timeout=300,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return Backend(False, "", "managed", docker_log, f"Could not run Alembic: {exc}")
        if mig.returncode == 0:
            break
        time.sleep(3)
    mig_log = f"{docker_log}\n\n{mig.stdout}\n{mig.stderr}".strip()
    if mig.returncode != 0:
        return Backend(False, "", "managed", mig_log,
                       "Database migration failed. Check that DATABASE settings in .env point to the host-published "
                       "PostgreSQL port (for example localhost), not a compose-internal hostname.")

    port = PREFERRED_PORT
    if _port_open(port):
        if _healthy(f"http://127.0.0.1:{port}{API_PREFIX}"):
            return Backend(True, f"http://127.0.0.1:{port}{API_PREFIX}", "managed", mig_log, port=port)
        port = _free_port()
    base = f"http://127.0.0.1:{port}{API_PREFIX}"

    logf = open(LOG_FILE, "wb")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=ROOT, stdout=logf, stderr=subprocess.STDOUT,
    )
    atexit.register(_stop, proc)

    deadline = time.time() + 90
    while time.time() < deadline:
        if proc.poll() is not None:
            break
        if _healthy(base):
            return Backend(True, base, "managed", mig_log, port=port)
        time.sleep(0.5)
    return Backend(False, base, "managed", mig_log,
                   "The API did not start. Redis, Qdrant or a setting in .env is the usual cause.\n\n" + _log_tail())


def render_boot_error(b: Backend) -> None:
    st.markdown('<div class="page-title">The workspace could not start</div>', unsafe_allow_html=True)
    st.error(b.error or "The backend is unavailable.")
    if b.migration_log:
        with st.expander("Startup output"):
            st.code(b.migration_log)
    if st.button("Try again", type="primary"):
        boot_backend.clear()
        st.rerun()


backend = boot_backend()
if not backend.ok:
    render_boot_error(backend)
    st.stop()
BASE = backend.base


# ----------------------------------------------------------------------------
# OpenAPI discovery: resolve routes and request fields from the live API
# ----------------------------------------------------------------------------
@st.cache_data(ttl=300, show_spinner=False)
def load_spec(base: str) -> dict:
    root = base[: -len(API_PREFIX)] if base.endswith(API_PREFIX) else base
    for url in (f"{root}/openapi.json", f"{base}/openapi.json"):
        try:
            r = requests.get(url, timeout=5)
            if r.ok:
                return r.json()
        except (requests.RequestException, ValueError):
            continue
    return {}


@dataclass
class Route:
    path: str
    op: dict

    @property
    def params(self) -> int:
        return len(re.findall(r"\{[^}]*\}", self.path))

    def fill(self, *vals: Any) -> str:
        n = self.params
        it = iter(list(vals[len(vals) - n:]) if n else [])
        return re.sub(r"\{[^}]*\}", lambda _m: str(next(it, "")), self.path)


def _norm(p: str) -> str:
    return re.sub(r"\{[^}]*\}", "{}", p).rstrip("/")


def route(method: str, *cands: str) -> Route:
    index: dict[str, tuple[str, dict]] = {}
    for p, ops in load_spec(BASE).get("paths", {}).items():
        rel = p[len(API_PREFIX):] if p.startswith(API_PREFIX) else p
        if method.lower() in ops:
            index.setdefault(_norm(rel), (rel, ops[method.lower()]))
    for c in cands:
        if _norm(c) in index:
            return Route(*index[_norm(c)])
    return Route(cands[0], {})


def route_multi(methods: tuple[str, ...], *cands: str) -> tuple[str, Route]:
    for m in methods:
        r = route(m, *cands)
        if r.op:
            return m, r
    return methods[0], route(methods[0], *cands)


def kb_paths(suffix: str = "") -> tuple[str, ...]:
    return tuple(f"{b}{suffix}" for b in KB_BASES)


def _deref(schema: Any, spec: dict) -> dict:
    for _ in range(8):
        if not isinstance(schema, dict):
            return {}
        meta = {k: schema[k] for k in ("description", "default", "title") if k in schema}
        if "$ref" in schema:
            schema = spec.get("components", {}).get("schemas", {}).get(schema["$ref"].split("/")[-1], {})
        elif len(schema.get("allOf", [])) == 1:
            schema = schema["allOf"][0]
        elif "anyOf" in schema or "oneOf" in schema:
            opts = [o for o in (schema.get("anyOf") or schema.get("oneOf")) if o.get("type") != "null"]
            schema = {**(opts[0] if opts else {}), **meta}
        else:
            return schema
    return schema if isinstance(schema, dict) else {}


def body_fields(r: Route, content: str = "application/json") -> tuple[dict, list[str]]:
    spec = load_spec(BASE)
    raw = (((r.op.get("requestBody") or {}).get("content") or {}).get(content) or {}).get("schema")
    s = _deref(raw or {}, spec)
    props = {k: _deref(v, spec) for k, v in (s.get("properties") or {}).items()}
    return props, list(s.get("required") or [])


def fit(props: dict, values: dict, fallback: tuple[str, ...] = ()) -> dict:
    """Keep only the keys the endpoint accepts (or the fallback keys when the schema is unknown)."""
    keys = props.keys() if props else fallback
    return {k: v for k, v in values.items() if k in keys and v not in (None, "")}


def pick_key(props: dict, names: tuple[str, ...], default: str) -> str:
    return next((n for n in names if n in props), default)


# ----------------------------------------------------------------------------
# HTTP client with token refresh
# ----------------------------------------------------------------------------
@dataclass
class Result:
    ok: bool
    status: int
    data: Any = None
    error: str = ""


def unwrap(d: Any) -> Any:
    if isinstance(d, dict) and "data" in d and any(k in d for k in ("success", "status", "message")):
        return d["data"]
    return d


def as_list(x: Any) -> list:
    x = unwrap(x)
    if isinstance(x, list):
        return x
    if isinstance(x, dict):
        for k in ("items", "results", "data", "records"):
            if isinstance(x.get(k), list):
                return x[k]
    return []


def _error_text(resp: requests.Response, payload: Any) -> str:
    if isinstance(payload, dict):
        detail = payload.get("detail", payload.get("message", payload.get("error")))
        if isinstance(detail, str):
            return detail
        if isinstance(detail, list):
            parts = []
            for e in detail:
                if isinstance(e, dict):
                    loc = ".".join(str(p) for p in (e.get("loc") or [])[1:])
                    parts.append(f"{loc}: {e.get('msg')}" if loc else str(e.get("msg")))
                else:
                    parts.append(str(e))
            return "; ".join(parts)
    return f"{resp.status_code} {resp.reason}"


def _store_tokens(data: Any) -> bool:
    d = unwrap(data)
    if isinstance(d, dict):
        d = d.get("tokens", d)
        access = d.get("access_token") or d.get("access")
        refresh = d.get("refresh_token") or d.get("refresh")
        if access:
            st.session_state["access_token"] = access
            if refresh:
                st.session_state["refresh_token"] = refresh
            return True
    return False


def _refresh() -> bool:
    rt = st.session_state.get("refresh_token")
    if not rt:
        return False
    res = call("POST", route("POST", "/auth/refresh").path, json_body={"refresh_token": rt}, auth=False, _retry=False)
    return res.ok and _store_tokens(res.data)


def call(method: str, path: str, *, params: dict | None = None, json_body: Any = None, data: dict | None = None,
         files: dict | None = None, auth: bool = True, timeout: int = 60, _retry: bool = True) -> Result:
    headers = {}
    if auth and st.session_state.get("access_token"):
        headers["Authorization"] = f"Bearer {st.session_state['access_token']}"
    try:
        resp = requests.request(method, BASE + path, params=params, json=json_body, data=data,
                                files=files, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        return Result(False, 0, error=f"Could not reach the API ({exc.__class__.__name__}).")
    if resp.status_code == 401 and auth and _retry:
        if _refresh():
            return call(method, path, params=params, json_body=json_body, data=data, files=files,
                        auth=auth, timeout=timeout, _retry=False)
        clear_session()
        st.session_state["flash"] = "Your session expired. Sign in again."
        st.rerun()
    try:
        payload = resp.json() if resp.content else None
    except ValueError:
        payload = None
    if resp.ok:
        return Result(True, resp.status_code, payload)
    return Result(False, resp.status_code, payload, _error_text(resp, payload))


def fetch_list(*cands: str, params: dict | None = None) -> tuple[list, Result]:
    r = route("GET", *cands)
    res = call("GET", r.path, params=params)
    return (as_list(res.data) if res.ok else []), res


def notify_error(res: Result, prefix: str = "") -> None:
    st.error(f"{prefix}{res.error}" if prefix else res.error)


# ----------------------------------------------------------------------------
# Session
# ----------------------------------------------------------------------------
def clear_session() -> None:
    for k in list(st.session_state.keys()):
        if k != "flash":
            del st.session_state[k]


def load_session() -> bool:
    res = call("GET", route("GET", "/auth/me").path)
    if not res.ok:
        return False
    user = unwrap(res.data) or {}
    org_id = user.get("organization_id") or (user.get("organization") or {}).get("id")
    st.session_state["user"] = user
    st.session_state["org_id"] = org_id
    if org_id:
        r = route("GET", "/organizations/{}")
        ores = call("GET", r.fill(org_id))
        if ores.ok:
            st.session_state["org"] = unwrap(ores.data) or {}
    return True


def sign_in(email: str, password: str) -> str | None:
    r = route("POST", "/auth/login")
    res = call("POST", r.path, json_body={"email": email, "password": password}, auth=False)
    if not res.ok:
        return res.error
    if not _store_tokens(res.data):
        return "The API signed you in but did not return a token."
    if not load_session():
        clear_session()
        return "Signed in, but your profile could not be loaded."
    return None


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "org"


def sign_up(full_name: str, email: str, password: str, org_id: str | None, org_name: str | None) -> str | None:
    if org_name:
        r = route("POST", "/organizations")
        props, _ = body_fields(r)
        body = fit(props, {"name": org_name, "slug": slugify(org_name)}, ("name",))
        res = call("POST", r.path, json_body=body, auth=False)
        if not res.ok:
            hint = ""
            if res.status in (401, 403):
                hint = " This deployment only lets signed-in users create organizations. Ask an admin for an organization ID and choose \"Join an existing organization\"."
            return f"Could not create the organization: {res.error}{hint}"
        org = unwrap(res.data) or {}
        org_id = org.get("id") or org.get("organization_id")
    r = route("POST", "/auth/register")
    props, _ = body_fields(r)
    body = fit(props, {"organization_id": org_id, "full_name": full_name, "email": email, "password": password},
               ("organization_id", "full_name", "email", "password"))
    res = call("POST", r.path, json_body=body, auth=False)
    if not res.ok:
        return f"Could not create the account: {res.error}"
    return sign_in(email, password)


def sign_out() -> None:
    rt = st.session_state.get("refresh_token")
    call("POST", route("POST", "/auth/logout").path, json_body={"refresh_token": rt} if rt else None, _retry=False)
    clear_session()


# ----------------------------------------------------------------------------
# UI helpers
# ----------------------------------------------------------------------------
def header(title: str, sub: str = "") -> None:
    sub_html = f'<div class="page-sub">{html.escape(sub)}</div>' if sub else ""
    st.markdown(f'<div class="page-title">{html.escape(title)}</div>{sub_html}', unsafe_allow_html=True)


def empty_state(title: str, body: str) -> None:
    st.markdown(f'<div class="empty"><h3>{html.escape(title)}</h3><div>{html.escape(body)}</div></div>',
                unsafe_allow_html=True)


def badge(text: str, tone: str = "neutral") -> str:
    return f'<span class="badge {tone}">{html.escape(text)}</span>'


def status_badge(status: Any) -> str:
    s = str(status or "").lower()
    if s in ("ready", "indexed", "completed", "complete", "processed", "done", "success"):
        return badge("Indexed", "ok")
    if s in ("pending", "processing", "queued", "uploaded", "indexing", "running"):
        return badge("Indexing", "warn")
    if s in ("failed", "error"):
        return badge("Failed", "bad")
    return badge(s.capitalize() or "Unknown")


def first(d: dict, *keys: str, default: Any = None) -> Any:
    for k in keys:
        v = d.get(k)
        if v not in (None, ""):
            return v
    return default


def label_of(name: str) -> str:
    base = name[:-3] if name.endswith("_id") else name
    return base.replace("_", " ").capitalize()


LONG_FIELDS = ("prompt", "instruction", "description", "content", "system", "about", "summary")
HIDDEN_FIELDS = {"id", "created_at", "updated_at", "is_deleted", "hashed_password"}


def render_fields(props: dict, required: list[str], key: str, *, prefill: dict | None = None,
                  defaults: dict | None = None, options: dict[str, list[tuple[str, Any]]] | None = None) -> dict:
    """Render form inputs from a JSON schema; returns the payload built from the inputs."""
    prefill, defaults, options = prefill or {}, defaults or {}, options or {}
    out: dict[str, Any] = {}
    for name, sch in props.items():
        if name in HIDDEN_FIELDS:
            continue
        if name in prefill:
            out[name] = prefill[name]
            continue
        req = name in required
        label = label_of(name) + ("" if req else " (optional)")
        help_ = sch.get("description")
        cur = defaults.get(name, sch.get("default"))
        k, typ = f"{key}:{name}", sch.get("type")

        if name in options:
            pairs = options[name]
            names = {v: n for n, v in pairs}
            if typ == "array":
                out[name] = st.multiselect(label, list(names), default=[v for v in (cur or []) if v in names],
                                           format_func=lambda v, m=names: m.get(v, str(v)), key=k, help=help_)
            else:
                vals = list(names) if req else ["", *names]
                idx = vals.index(cur) if cur in vals else 0
                out[name] = st.selectbox(label, vals, index=idx, key=k, help=help_,
                                         format_func=lambda v, m=names: m.get(v, "None"))
        elif sch.get("enum"):
            vals = list(sch["enum"])
            out[name] = st.selectbox(label, vals, index=vals.index(cur) if cur in vals else 0, key=k, help=help_)
        elif typ == "boolean":
            out[name] = st.toggle(label, value=bool(cur), key=k, help=help_)
        elif typ == "integer":
            lo, hi = sch.get("minimum"), sch.get("maximum")
            out[name] = st.number_input(label, min_value=int(lo) if lo is not None else None,
                                        max_value=int(hi) if hi is not None else None,
                                        value=int(cur if cur is not None else (lo or 0)), step=1, key=k, help=help_)
        elif typ == "number":
            lo, hi = sch.get("minimum"), sch.get("maximum")
            out[name] = st.number_input(label, min_value=float(lo) if lo is not None else None,
                                        max_value=float(hi) if hi is not None else None,
                                        value=float(cur if cur is not None else (lo or 0.0)), step=0.1, key=k, help=help_)
        elif typ == "array":
            raw = st.text_input(label + " (comma separated)", value=", ".join(map(str, cur or [])), key=k, help=help_)
            out[name] = [x.strip() for x in raw.split(",") if x.strip()]
        elif typ == "object":
            raw = st.text_area(label + " (JSON)", value=json.dumps(cur or {}, indent=2), key=k, help=help_)
            try:
                out[name] = json.loads(raw) if raw.strip() else {}
            except json.JSONDecodeError:
                out[name] = raw
        else:
            secret = "password" in name or sch.get("format") == "password"
            if any(w in name for w in LONG_FIELDS) and not secret:
                tall = any(w in name for w in ("prompt", "instruction"))
                val = st.text_area(label, value=str(cur or ""), height=170 if tall else 90, key=k, help=help_)
            else:
                val = st.text_input(label, value=str(cur or ""), type="password" if secret else "default",
                                    key=k, help=help_)
            if val.strip() or req:
                out[name] = val.strip()
    return out


def missing_fields(payload: dict, required: list[str]) -> list[str]:
    return [label_of(n) for n in required if n in payload and payload[n] in ("", None, [])]


def kb_options(kbs: list) -> list[tuple[str, Any]]:
    return [(first(k, "name", "title", default="Untitled"), k.get("id")) for k in kbs]


def options_for(props: dict, kbs: list) -> dict:
    return {n: kb_options(kbs) for n in props if "knowledge_base" in n or n in ("kb_id", "kb_ids")}


def confirm_delete(label: str, key: str, noun: str) -> bool:
    with st.popover(label, use_container_width=False):
        st.write(f"Delete this {noun}? This can't be undone.")
        return st.button(f"Delete {noun}", type="primary", key=key)
    return False


# ----------------------------------------------------------------------------
# Chunk / source rendering
# ----------------------------------------------------------------------------
def norm_chunk(c: Any) -> dict:
    if isinstance(c, str):
        return {"text": c, "score": None, "doc": None, "page": None}
    meta = c.get("metadata") or c.get("payload") or {}

    def g(*keys: str) -> Any:
        for k in keys:
            for src in (c, meta):
                if isinstance(src, dict) and src.get(k) not in (None, ""):
                    return src[k]
        return None

    score = g("score", "relevance", "rerank_score", "similarity")
    try:
        score = float(score) if score is not None else None
    except (TypeError, ValueError):
        score = None
    return {"text": str(g("content", "text", "chunk", "page_content", "chunk_text") or ""), "score": score,
            "doc": g("document_name", "filename", "file_name", "source", "title", "document_id"),
            "page": g("page", "page_number", "page_label")}


def percentages(chunks: list[dict]) -> list[float | None]:
    vals = [c["score"] for c in chunks if c["score"] is not None]
    if not vals:
        return [None] * len(chunks)
    if min(vals) >= 0 and max(vals) <= 1:
        return [None if c["score"] is None else c["score"] * 100 for c in chunks]
    top = max(vals) or 1
    return [None if c["score"] is None else max(0.0, c["score"] / top * 100) for c in chunks]


def passage_html(c: dict, pct: float | None) -> str:
    doc = html.escape(str(c["doc"])) if c["doc"] else "Source"
    page = f'<span class="muted">Page {html.escape(str(c["page"]))}</span>' if c["page"] else ""
    meter = f'<span class="meter" title="Relevance"><i style="width:{pct:.0f}%"></i></span>' if pct is not None else ""
    lines = [html.escape(l.strip()) for l in c["text"].splitlines() if l.strip()]
    return (f'<div class="passage"><div class="passage-head"><strong>{doc}</strong>{page}{meter}</div>'
            f'<div class="passage-text">{"<br>".join(lines)}</div></div>')


def render_passages(raw_chunks: list) -> None:
    chunks = [norm_chunk(c) for c in raw_chunks]
    for c, pct in zip(chunks, percentages(chunks)):
        st.markdown(passage_html(c, pct), unsafe_allow_html=True)


def find_first(d: Any, keys: tuple[str, ...], kind: type) -> Any:
    if not isinstance(d, dict):
        return None
    for k in keys:
        if isinstance(d.get(k), kind) and d[k]:
            return d[k]
    return None


# ----------------------------------------------------------------------------
# Authentication screen
# ----------------------------------------------------------------------------
def auth_screen() -> None:
    st.markdown("<style>section[data-testid='stSidebar']{display:none}</style>", unsafe_allow_html=True)
    left, right = st.columns([1.15, 1], gap="large")
    with left:
        st.markdown(
            """<div class="auth-panel">
            <div class="mark">AIOS</div>
            <h1>Every answer, traced to its source.</h1>
            <p>Upload your team's documents, ask questions in plain language, and see the exact passages behind each answer.</p>
            <div class="auth-demo">
              <div class="q">Example question: What is the refund window for annual plans?</div>
              <div class="a">Annual plans can be refunded within 30 days of purchase.</div>
              <div class="src">Refund policy, page 2</div>
            </div></div>""",
            unsafe_allow_html=True,
        )
    with right:
        st.write("")
        if st.session_state.get("flash"):
            st.warning(st.session_state.pop("flash"))
        st.markdown('<div class="page-title">Welcome</div><div class="page-sub">Sign in to your workspace or create an account.</div>',
                    unsafe_allow_html=True)
        tab_in, tab_up = st.tabs(["Sign in", "Create account"])
        with tab_in:
            with st.form("signin"):
                email = st.text_input("Email", autocomplete="email")
                password = st.text_input("Password", type="password", autocomplete="current-password")
                go = st.form_submit_button("Sign in", type="primary", use_container_width=True)
            if go:
                if not email or not password:
                    st.error("Enter your email and password.")
                else:
                    with st.spinner("Signing in…"):
                        err = sign_in(email.strip(), password)
                    if err:
                        st.error(err)
                    else:
                        st.rerun()
        with tab_up:
            mode = st.radio("Organization", ["Start a new organization", "Join an existing organization"],
                            label_visibility="collapsed")
            with st.form("signup"):
                if mode.startswith("Start"):
                    org_name = st.text_input("Organization name")
                    org_id = None
                else:
                    org_id = st.text_input("Organization ID", help="Ask an admin of the organization for its ID.")
                    org_name = None
                full_name = st.text_input("Full name")
                email_u = st.text_input("Work email", autocomplete="email")
                pw_u = st.text_input("Password", type="password", autocomplete="new-password")
                go_u = st.form_submit_button("Create account", type="primary", use_container_width=True)
            if go_u:
                if not (full_name and email_u and pw_u and (org_name or org_id)):
                    st.error("Fill in every field to continue.")
                else:
                    with st.spinner("Creating your workspace…"):
                        err = sign_up(full_name.strip(), email_u.strip(), pw_u,
                                      org_id.strip() if org_id else None, org_name.strip() if org_name else None)
                    if err:
                        st.error(err)
                    else:
                        st.rerun()


# ----------------------------------------------------------------------------
# Chat
# ----------------------------------------------------------------------------
def norm_message(m: dict) -> dict:
    meta = m.get("metadata") or m.get("meta") or {}
    return {
        "role": str(m.get("role") or m.get("sender") or "").lower().split(".")[-1],
        "content": first(m, "content", "text", "message", default=""),
        "sources": first(m, "sources", "citations") or (meta.get("sources") if isinstance(meta, dict) else None),
        "tool_calls": first(m, "tool_calls", "tools_used") or (meta.get("tool_calls") if isinstance(meta, dict) else None),
        "created_at": m.get("created_at") or "",
    }


def fetch_messages(conv_id: Any) -> list[dict] | None:
    r = route("GET", "/conversations/{}/messages", "/messages")
    res = call("GET", r.fill(conv_id), params=None if r.params else {"conversation_id": conv_id})
    if not res.ok:
        return None
    msgs = [norm_message(m) for m in as_list(res.data) if isinstance(m, dict)]
    return sorted(msgs, key=lambda m: m["created_at"])


def parse_reply(data: Any) -> dict | None:
    d = unwrap(data)
    if isinstance(d, list):
        for m in reversed(d):
            if isinstance(m, dict) and norm_message(m)["role"] == "assistant":
                return norm_message(m)
        return None
    if not isinstance(d, dict):
        return None
    for k in ("assistant_message", "assistant", "reply", "ai_message"):
        if isinstance(d.get(k), dict):
            return {**norm_message(d[k]), "role": "assistant"}
    nm = norm_message(d)
    if nm["content"] and nm["role"] != "user":
        return {**nm, "role": "assistant"}
    text = find_first(d, ("answer", "response", "output"), str)
    if text:
        return {"role": "assistant", "content": text, "sources": d.get("sources"), "tool_calls": d.get("tool_calls"),
                "created_at": ""}
    return None


def render_message(m: dict) -> None:
    if m["role"] not in ("user", "assistant"):
        return
    with st.chat_message(m["role"]):
        st.markdown(str(m["content"]))
        if m["role"] == "assistant":
            if m.get("tool_calls"):
                calls = m["tool_calls"] if isinstance(m["tool_calls"], list) else [m["tool_calls"]]
                names = [str(first(c, "name", "tool", default="tool")) if isinstance(c, dict) else str(c) for c in calls]
                with st.expander(f"Used {len(names)} tool{'s' if len(names) != 1 else ''}"):
                    st.write(", ".join(names))
            if m.get("sources"):
                srcs = m["sources"] if isinstance(m["sources"], list) else [m["sources"]]
                with st.expander(f"{len(srcs)} source{'s' if len(srcs) != 1 else ''}"):
                    render_passages(srcs)


def create_conversation(agent: dict, title: str) -> Any | None:
    r = route("POST", "/conversations")
    props, _ = body_fields(r)
    user = st.session_state.get("user", {})
    body = fit(props, {"title": title[:60], "agent_id": agent.get("id"),
                       "organization_id": st.session_state.get("org_id"), "user_id": user.get("id")},
               ("title", "agent_id"))
    res = call("POST", r.path, json_body=body)
    if not res.ok:
        notify_error(res, "Could not start the chat. ")
        return None
    d = unwrap(res.data) or {}
    return d.get("id") or d.get("conversation_id")


def send_message(conv_id: Any, agent: dict, text: str) -> Result:
    r = route("POST", "/conversations/{}/messages", "/messages")
    props, _ = body_fields(r)
    content_key = pick_key(props, ("content", "message", "text", "query"), "content")
    body = fit(props, {content_key: text, "role": "user", "conversation_id": conv_id, "agent_id": agent.get("id")},
               (content_key, "role", "conversation_id"))
    return call("POST", r.fill(conv_id), json_body=body, timeout=240)


SUGGESTIONS = (
    "What documents do you have access to?",
    "Summarize the most important points across our documents.",
    "What should a new teammate read first?",
)


def page_chat() -> None:
    agents, res = fetch_list("/agents")
    if not res.ok:
        header("Chat")
        notify_error(res, "Could not load agents. ")
        return
    if not agents:
        header("Chat", "Chat with an agent that answers from your knowledge bases.")
        empty_state("Create your first agent", "An agent combines instructions with the knowledge it can use.")
        if st.button("Go to Agents", type="primary"):
            st.switch_page(PAGES["agents"])
        return

    ids = [a["id"] for a in agents]
    if st.session_state.get("agent_id") not in ids:
        st.session_state["agent_id"] = ids[0]
    threads: dict = st.session_state.setdefault("threads", {})

    left, right = st.columns([1, 3.1], gap="large")
    with left:
        agent_id = st.selectbox("Agent", ids, key="agent_id",
                                format_func=lambda i: first(next(a for a in agents if a["id"] == i), "name", default="Agent"))
        if st.session_state.get("_conv_agent") != agent_id:
            st.session_state["conv_id"] = None
            st.session_state["_conv_agent"] = agent_id
        if st.button("New chat", icon=":material/add:", type="primary", use_container_width=True):
            st.session_state["conv_id"] = None
            st.rerun()
        convs, _ = fetch_list("/conversations", params={"agent_id": agent_id})
        convs = [c for c in convs if str(c.get("agent_id", agent_id)) == str(agent_id)]
        convs.sort(key=lambda c: str(c.get("updated_at") or c.get("created_at") or ""), reverse=True)
        st.markdown('<div class="section-title">Recent chats</div>', unsafe_allow_html=True)
        if not convs:
            st.markdown('<div class="muted">No chats yet with this agent.</div>', unsafe_allow_html=True)
        for c in convs[:30]:
            title = str(first(c, "title", "name", default="Untitled chat"))
            selected = str(st.session_state.get("conv_id")) == str(c["id"])
            if st.button(title[:40], key=f"conv-{c['id']}", use_container_width=True,
                         type="primary" if selected else "secondary"):
                st.session_state["conv_id"] = c["id"]
                st.rerun()

    agent = next(a for a in agents if a["id"] == agent_id)
    conv_id = st.session_state.get("conv_id")
    if conv_id and conv_id not in threads:
        loaded = fetch_messages(conv_id)
        threads[conv_id] = loaded if loaded is not None else []

    pending = st.session_state.pop("_pending_prompt", None)
    prompt = st.chat_input(f"Message {first(agent, 'name', default='the agent')}") or pending

    with right:
        top, menu = st.columns([6, 1])
        with top:
            st.markdown(f'<div class="page-title" style="font-size:1.35rem">{html.escape(str(first(agent, "name", default="Agent")))}</div>'
                        f'<div class="page-sub" style="margin-bottom:.6rem">{html.escape(str(first(agent, "description", default="")))}</div>',
                        unsafe_allow_html=True)
        if conv_id:
            with menu:
                if confirm_delete("Delete", "del-conv", "chat"):
                    r = route("DELETE", "/conversations/{}")
                    d = call("DELETE", r.fill(conv_id))
                    if d.ok:
                        threads.pop(conv_id, None)
                        st.session_state["conv_id"] = None
                        st.rerun()
                    notify_error(d)

        thread = threads.get(conv_id, []) if conv_id else []
        if not thread and not prompt:
            st.markdown('<div class="empty"><h3>What would you like to know?</h3>'
                        '<div>Answers come with the passages they were based on.</div></div>', unsafe_allow_html=True)
            cols = st.columns(len(SUGGESTIONS))
            for col, text in zip(cols, SUGGESTIONS):
                if col.button(text, key=f"sug-{text}", use_container_width=True):
                    st.session_state["_pending_prompt"] = text
                    st.rerun()
        for m in thread:
            render_message(m)

        if prompt:
            if not conv_id:
                conv_id = create_conversation(agent, prompt)
                if not conv_id:
                    return
                st.session_state["conv_id"] = conv_id
                threads[conv_id] = []
            user_msg = {"role": "user", "content": prompt, "sources": None, "tool_calls": None, "created_at": ""}
            render_message(user_msg)
            with st.chat_message("assistant"):
                with st.spinner("Thinking…"):
                    res = send_message(conv_id, agent, prompt)
            if not res.ok:
                notify_error(res, "The agent could not answer. ")
                threads[conv_id].append(user_msg)
                return
            reply = parse_reply(res.data)
            server = fetch_messages(conv_id)
            if server:
                threads[conv_id] = server
            else:
                threads[conv_id] += [user_msg] + ([reply] if reply else [])
            st.rerun()


# ----------------------------------------------------------------------------
# Knowledge bases and documents
# ----------------------------------------------------------------------------
def fetch_documents(kb_id: Any) -> tuple[list, Result]:
    r = route("GET", *kb_paths("/{}/documents"), "/documents")
    res = call("GET", r.fill(kb_id), params=None if r.params else {"knowledge_base_id": kb_id})
    return (as_list(res.data) if res.ok else []), res


def upload_pdf(kb_id: Any, f: Any) -> Result:
    r = route("POST", *kb_paths("/{}/documents"), *kb_paths("/{}/documents/upload"), "/documents/upload", "/documents")
    props, _ = body_fields(r, "multipart/form-data")
    file_key = next((k for k, v in props.items()
                     if v.get("format") == "binary" or "file" in k), "file")
    stem = Path(f.name).stem
    form = fit({k: v for k, v in props.items() if k != file_key},
               {"knowledge_base_id": kb_id, "kb_id": kb_id, "title": stem, "name": f.name, "filename": f.name},
               () if r.params else ("knowledge_base_id",))
    form = {k: str(v) for k, v in form.items()}
    return call("POST", r.fill(kb_id), data=form, files={file_key: (f.name, f.getvalue(), "application/pdf")}, timeout=300)


def docs_fragment(kb_id: Any) -> None:
    docs, res = fetch_documents(kb_id)
    if not res.ok:
        notify_error(res, "Could not load documents. ")
        return
    busy = any(str(first(d, "status", "state", default="")).lower() in
               ("pending", "processing", "queued", "uploaded", "indexing", "running") for d in docs)
    was_busy = st.session_state.get("_docs_busy", False)
    st.session_state["_docs_busy"] = busy
    if was_busy and not busy:
        st.rerun()

    head, refresh = st.columns([6, 1])
    head.markdown(f'<div class="section-title">{len(docs)} document{"s" if len(docs) != 1 else ""}</div>',
                  unsafe_allow_html=True)
    if refresh.button("Refresh", key="docs-refresh", icon=":material/refresh:"):
        st.rerun(scope="fragment")
    if not docs:
        empty_state("No documents yet", "Upload a PDF above and it will be indexed for search and chat.")
        return
    for d in docs:
        c1, c2, c3, c4 = st.columns([5, 1.6, 1.6, 0.8], vertical_alignment="center")
        name = first(d, "original_filename", "filename", "file_name", "name", "title", default="Untitled document")
        c1.markdown(f"**{html.escape(str(name))}**", unsafe_allow_html=True)
        c2.markdown(status_badge(first(d, "status", "state")), unsafe_allow_html=True)
        c3.markdown(f'<span class="muted">{html.escape(str(d.get("created_at", ""))[:10])}</span>', unsafe_allow_html=True)
        if c4.button("", key=f"deldoc-{d['id']}", icon=":material/delete:", type="tertiary", help="Delete document"):
            r = route("DELETE", "/documents/{}", *kb_paths("/{}/documents/{}"))
            dres = call("DELETE", r.fill(kb_id, d["id"]))
            if dres.ok:
                st.toast("Document deleted")
                st.rerun(scope="fragment")
            notify_error(dres)


def page_knowledge() -> None:
    header("Knowledge", "Organize documents into knowledge bases that agents can search.")
    kbs, res = fetch_list(*KB_BASES)
    if not res.ok:
        notify_error(res, "Could not load knowledge bases. ")
        return
    org_id = st.session_state.get("org_id")

    with st.expander("New knowledge base", expanded=not kbs):
        r = route("POST", *KB_BASES)
        props, req = body_fields(r)
        props = props or {"name": {"type": "string"}, "description": {"type": "string"}}
        req = req or ["name"]
        with st.form("new-kb", clear_on_submit=True):
            payload = render_fields(props, req, "newkb", prefill={"organization_id": org_id})
            go = st.form_submit_button("Create knowledge base", type="primary")
        if go:
            miss = missing_fields(payload, req)
            if miss:
                st.error(f"Fill in: {', '.join(miss)}.")
            else:
                cres = call("POST", r.path, json_body=payload)
                if cres.ok:
                    st.session_state["kb_id"] = (unwrap(cres.data) or {}).get("id")
                    st.toast("Knowledge base created")
                    st.rerun()
                notify_error(cres)
    if not kbs:
        return

    ids = [k["id"] for k in kbs]
    if st.session_state.get("kb_id") not in ids:
        st.session_state["kb_id"] = ids[0]
    left, right = st.columns([1, 3], gap="large")
    with left:
        st.markdown('<div class="section-title">Knowledge bases</div>', unsafe_allow_html=True)
        for k in kbs:
            sel = st.session_state["kb_id"] == k["id"]
            if st.button(str(first(k, "name", "title", default="Untitled")), key=f"kb-{k['id']}",
                         type="primary" if sel else "secondary", use_container_width=True):
                st.session_state["kb_id"] = k["id"]
                st.rerun()

    kb = next(k for k in kbs if k["id"] == st.session_state["kb_id"])
    with right:
        st.markdown(f'<div class="page-title" style="font-size:1.35rem">{html.escape(str(first(kb, "name", "title", default="Untitled")))}</div>'
                    f'<div class="page-sub" style="margin-bottom:.6rem">{html.escape(str(first(kb, "description", default="")))}</div>',
                    unsafe_allow_html=True)
        tab_docs, tab_settings = st.tabs(["Documents", "Settings"])
        with tab_docs:
            files = st.file_uploader("Add PDF documents", type=["pdf"], accept_multiple_files=True,
                                     key=f"up-{kb['id']}-{st.session_state.get('_up_gen', 0)}")
            if files and st.button("Upload and index", type="primary"):
                with st.status("Uploading documents…", expanded=True) as status:
                    failed = 0
                    for f in files:
                        ures = upload_pdf(kb["id"], f)
                        if ures.ok:
                            st.write(f"Uploaded {f.name}")
                        else:
                            failed += 1
                            st.write(f"Could not upload {f.name}: {ures.error}")
                    status.update(label="Upload finished" if not failed else f"{failed} upload(s) failed",
                                  state="complete" if not failed else "error")
                st.session_state["_up_gen"] = st.session_state.get("_up_gen", 0) + 1
                if not failed:
                    st.rerun()
            runner = st.fragment(run_every=3 if st.session_state.get("_docs_busy") else None)(docs_fragment)
            runner(kb["id"])
        with tab_settings:
            m, r = route_multi(("PATCH", "PUT"), *[f"{b}/{{}}" for b in KB_BASES])
            props, req = body_fields(r)
            props = props or {"name": {"type": "string"}, "description": {"type": "string"}}
            with st.form("edit-kb"):
                payload = render_fields(props, req, f"editkb{kb['id']}", defaults=kb,
                                        prefill={"organization_id": st.session_state.get("org_id")})
                saved = st.form_submit_button("Save changes", type="primary")
            if saved:
                sres = call(m, r.fill(kb["id"]), json_body=payload)
                if sres.ok:
                    st.toast("Changes saved")
                    st.rerun()
                notify_error(sres)
            st.markdown('<div class="section-title">Delete knowledge base</div>', unsafe_allow_html=True)
            st.markdown('<div class="muted">Removes the knowledge base and its indexed documents.</div>', unsafe_allow_html=True)
            if confirm_delete("Delete knowledge base", "del-kb", "knowledge base"):
                dr = route("DELETE", *[f"{b}/{{}}" for b in KB_BASES])
                dres = call("DELETE", dr.fill(kb["id"]))
                if dres.ok:
                    st.toast("Knowledge base deleted")
                    st.rerun()
                notify_error(dres)


# ----------------------------------------------------------------------------
# Knowledge search
# ----------------------------------------------------------------------------
def page_search() -> None:
    header("Knowledge search", "See exactly which passages are retrieved for a question, before an agent uses them.")
    kbs, _ = fetch_list(*KB_BASES)
    r = route("POST", "/query")
    props, req = body_fields(r)
    q_key = pick_key(props, ("query", "question", "text", "q"), "query")
    kb_key = pick_key(props, ("knowledge_base_id", "kb_id"), "knowledge_base_id")
    k_key = next((k for k in ("top_k", "limit", "k") if k in props), None)

    with st.form("search"):
        question = st.text_input("Question", placeholder="Ask something your documents can answer")
        c1, c2 = st.columns([3, 1])
        names = {v: n for n, v in kb_options(kbs)}
        needs_kb = kb_key in req
        choices = list(names) if needs_kb else ["", *names]
        kb_choice = c1.selectbox("Knowledge base", choices, format_func=lambda v: names.get(v, "All knowledge bases"))
        top_k = c2.slider("Passages", 1, 20, 5) if k_key else None
        go = st.form_submit_button("Search", type="primary")

    if go:
        if not question.strip():
            st.error("Enter a question to search.")
        else:
            body = fit(props, {q_key: question.strip(), kb_key: kb_choice, k_key: top_k,
                               "organization_id": st.session_state.get("org_id")}, (q_key, kb_key))
            with st.spinner("Searching…"):
                res = call("POST", r.path, json_body=body, timeout=240)
            st.session_state["last_search"] = (question.strip(), res)

    last = st.session_state.get("last_search")
    if not last:
        empty_state("Nothing searched yet", "Results show the retrieved context and every source passage.")
        return
    q, res = last
    if not res.ok:
        notify_error(res, "Search failed. ")
        return
    d = unwrap(res.data)
    answer = find_first(d, ("answer", "response", "result", "output", "text"), str)
    context = find_first(d, ("context", "compressed_context", "contexts"), (str, list))
    raw_chunks = find_first(d, ("sources", "chunks", "source_chunks", "results", "documents", "passages"), list)
    if isinstance(d, list):
        raw_chunks = d

    if answer:
        st.markdown('<div class="section-title">Answer</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="answer">{html.escape(answer).replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
    if raw_chunks:
        st.markdown(f'<div class="section-title">{len(raw_chunks)} source passage{"s" if len(raw_chunks) != 1 else ""}</div>',
                    unsafe_allow_html=True)
        render_passages(raw_chunks)
    if context:
        with st.expander("Retrieved context sent to the model"):
            st.markdown("\n\n".join(map(str, context)) if isinstance(context, list) else context)
    if not (answer or raw_chunks or context):
        empty_state("No matching passages", "Try rephrasing the question or check that documents have finished indexing.")
    with st.expander("Raw response"):
        st.json(d)


# ----------------------------------------------------------------------------
# Agents
# ----------------------------------------------------------------------------
def page_agents() -> None:
    header("Agents", "Agents combine instructions with the knowledge and tools they can use.")
    agents, res = fetch_list("/agents")
    if not res.ok:
        notify_error(res, "Could not load agents. ")
        return
    kbs, _ = fetch_list(*KB_BASES)
    org_id = st.session_state.get("org_id")

    with st.expander("New agent", expanded=not agents):
        r = route("POST", "/agents")
        props, req = body_fields(r)
        props = props or {"name": {"type": "string"}, "description": {"type": "string"},
                          "system_prompt": {"type": "string"}}
        req = req or ["name"]
        with st.form("new-agent", clear_on_submit=True):
            payload = render_fields(props, req, "newagent", prefill={"organization_id": org_id},
                                    options=options_for(props, kbs))
            go = st.form_submit_button("Create agent", type="primary")
        if go:
            miss = missing_fields(payload, req)
            if miss:
                st.error(f"Fill in: {', '.join(miss)}.")
            else:
                cres = call("POST", r.path, json_body=payload)
                if cres.ok:
                    st.toast("Agent created")
                    st.rerun()
                notify_error(cres)

    if not agents:
        return
    m, er = route_multi(("PATCH", "PUT"), "/agents/{}")
    eprops, ereq = body_fields(er)
    eprops = eprops or {"name": {"type": "string"}, "description": {"type": "string"},
                        "system_prompt": {"type": "string"}}
    kb_names = {k.get("id"): first(k, "name", "title", default="") for k in kbs}
    cols = st.columns(2, gap="medium")
    for i, a in enumerate(agents):
        with cols[i % 2], st.container(border=True):
            st.markdown(f"**{html.escape(str(first(a, 'name', default='Untitled agent')))}**", unsafe_allow_html=True)
            st.markdown(f'<div class="agent-desc">{html.escape(str(first(a, "description", default="No description.")))}</div>',
                        unsafe_allow_html=True)
            linked = [a.get(k) for k in ("knowledge_base_id", "kb_id") if a.get(k)] + list(a.get("knowledge_base_ids") or [])
            tags = " ".join(badge(kb_names.get(x, "Knowledge base")) for x in linked)
            if tags:
                st.markdown(tags, unsafe_allow_html=True)
            with st.expander("Edit"):
                with st.form(f"edit-agent-{a['id']}"):
                    body = render_fields(eprops, ereq, f"agent{a['id']}", defaults=a,
                                         prefill={"organization_id": org_id}, options=options_for(eprops, kbs))
                    saved = st.form_submit_button("Save changes", type="primary")
                if saved:
                    sres = call(m, er.fill(a["id"]), json_body=body)
                    if sres.ok:
                        st.toast("Agent updated")
                        st.rerun()
                    notify_error(sres)
                if confirm_delete("Delete agent", f"del-agent-{a['id']}", "agent"):
                    dres = call("DELETE", route("DELETE", "/agents/{}").fill(a["id"]))
                    if dres.ok:
                        st.toast("Agent deleted")
                        st.rerun()
                    notify_error(dres)


# ----------------------------------------------------------------------------
# Organization
# ----------------------------------------------------------------------------
def page_organization() -> None:
    header("Organization", "Everything in the workspace belongs to your organization.")
    org_id = st.session_state.get("org_id")
    if not org_id:
        empty_state("No organization", "Your account is not attached to an organization.")
        return
    gr = route("GET", "/organizations/{}")
    res = call("GET", gr.fill(org_id))
    if not res.ok:
        notify_error(res, "Could not load the organization. ")
        return
    org = unwrap(res.data) or {}
    st.session_state["org"] = org

    m, er = route_multi(("PATCH", "PUT"), "/organizations/{}")
    props, req = body_fields(er)
    props = props or {"name": {"type": "string"}}
    st.markdown('<div class="section-title">Details</div>', unsafe_allow_html=True)
    with st.form("edit-org"):
        payload = render_fields(props, req, "org", defaults=org)
        saved = st.form_submit_button("Save changes", type="primary")
    if saved:
        sres = call(m, er.fill(org_id), json_body=payload)
        if sres.ok:
            st.toast("Organization updated")
            load_session()
            st.rerun()
        notify_error(sres)
    st.caption(f"Organization ID: {org_id}")

    orgs, lres = fetch_list("/organizations")
    if lres.ok and len(orgs) > 1:
        st.markdown('<div class="section-title">All organizations you can access</div>', unsafe_allow_html=True)
        st.dataframe([{"Name": first(o, "name", default=""), "ID": o.get("id")} for o in orgs],
                     use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">Delete organization</div>', unsafe_allow_html=True)
    st.markdown('<div class="muted">Permanently removes the organization and its data. Type its name to confirm.</div>',
                unsafe_allow_html=True)
    name = str(first(org, "name", default=""))
    typed = st.text_input("Organization name", key="org-del-confirm", label_visibility="collapsed",
                          placeholder=name or "Organization name")
    if st.button("Delete organization", disabled=not name or typed.strip() != name):
        dres = call("DELETE", route("DELETE", "/organizations/{}").fill(org_id))
        if dres.ok:
            clear_session()
            st.session_state["flash"] = "The organization was deleted."
            st.rerun()
        notify_error(dres)


# ----------------------------------------------------------------------------
# System
# ----------------------------------------------------------------------------
def page_system() -> None:
    header("System", "Status of the API and database migrations behind this workspace.")
    healthy = _healthy(BASE, 3)
    c1, c2, c3 = st.columns(3)
    c1.metric("API", "Healthy" if healthy else "Unreachable")
    c2.metric("Mode", "External API" if backend.mode == "external" else "Managed by this app")
    c3.metric("Endpoint", BASE.replace("http://", ""))
    root = BASE[: -len(API_PREFIX)] if BASE.endswith(API_PREFIX) else BASE
    st.markdown(f"[Open API reference]({root}/docs)")
    if backend.migration_log:
        with st.expander("Startup output"):
            st.code(backend.migration_log)
    if backend.mode == "managed":
        with st.expander("API log"):
            st.code(_log_tail(80) or "No log output yet.")
        if st.button("Restart API"):
            boot_backend.clear()
            load_spec.clear()
            st.rerun()


# ----------------------------------------------------------------------------
# App shell
# ----------------------------------------------------------------------------
def sidebar_footer() -> None:
    user = st.session_state.get("user", {})
    name = str(first(user, "full_name", "name", "email", default="Account"))
    org = str(first(st.session_state.get("org", {}), "name", default=""))
    initials = "".join(w[0] for w in name.split()[:2]).upper() or "A"
    with st.sidebar:
        st.markdown(f'<div class="userchip"><div class="av">{html.escape(initials)}</div><div class="who">'
                    f'<b>{html.escape(name)}</b><span>{html.escape(org or str(user.get("email", "")))}</span></div></div>',
                    unsafe_allow_html=True)
        if st.button("Sign out", icon=":material/logout:", use_container_width=True):
            sign_out()
            st.rerun()


PAGES = {
    "chat": st.Page(page_chat, title="Chat", icon=":material/chat:", url_path="chat", default=True),
    "knowledge": st.Page(page_knowledge, title="Knowledge", icon=":material/library_books:", url_path="knowledge"),
    "search": st.Page(page_search, title="Knowledge search", icon=":material/search:", url_path="search"),
    "agents": st.Page(page_agents, title="Agents", icon=":material/smart_toy:", url_path="agents"),
    "organization": st.Page(page_organization, title="Organization", icon=":material/apartment:", url_path="organization"),
    "system": st.Page(page_system, title="System", icon=":material/monitor_heart:", url_path="system"),
}


def main() -> None:
    if not st.session_state.get("access_token"):
        auth_screen()
        st.stop()
    if "user" not in st.session_state and not load_session():
        clear_session()
        st.rerun()
    nav = st.navigation({
        "Workspace": [PAGES["chat"], PAGES["knowledge"], PAGES["search"]],
        "Configure": [PAGES["agents"], PAGES["organization"], PAGES["system"]],
    })
    sidebar_footer()
    nav.run()


main()