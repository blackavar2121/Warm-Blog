#!/usr/bin/env python3
"""
Bricolage Now Updater
Serves a local form at http://localhost:8787 — edit the Now panel fields and
hit Save. Writes the changes straight back to config.json.

Usage:
    python3 now-updater.py            # uses ./config.json
    python3 now-updater.py /path/to/config.json
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

PORT = 8787
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

if len(sys.argv) > 1:
    CONFIG_PATH = os.path.abspath(sys.argv[1])


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")


def esc(s):
    return str(s).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def field(label, name, value="", kind="text", placeholder=""):
    val = esc(str(value) if value is not None else "")
    ph = f' placeholder="{esc(placeholder)}"' if placeholder else ""
    return (
        f'<label>{label}'
        f'<input type="{kind}" name="{name}" value="{val}"{ph}>'
        f"</label>"
    )


def render_form(cfg):
    now = cfg.get("params", {}).get("now", {})
    r = now.get("reading", {})
    p = now.get("playing", {})
    a = now.get("activity", {})

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bricolage · Now Updater</title>
<style>
  :root {{
    --terra:#b5563a; --burnt:#c2622d; --bg:#f5ede0; --surface:#fbf6ec;
    --ink:#3a3630; --ink-soft:#6b6357; --ink-faint:#9a9183;
    --hair:#e2d7c4; --hair-strong:#d4c6ad;
    --serif:"Georgia","Times New Roman",serif;
    --mono:"JetBrains Mono",ui-monospace,monospace;
  }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ background:var(--bg); color:var(--ink); font-family:var(--serif);
    font-size:16px; line-height:1.5; -webkit-font-smoothing:antialiased; }}
  header {{ position:sticky; top:0; height:52px; background:var(--bg);
    border-bottom:1px solid var(--hair); display:flex; align-items:center;
    padding:0 28px; gap:14px; }}
  header::before {{ content:""; position:absolute; top:0; left:0; right:0;
    height:4px; background:var(--terra); }}
  header h1 {{ font-size:18px; font-weight:600; color:var(--burnt); }}
  header .path {{ font-family:var(--mono); font-size:11px;
    color:var(--ink-faint); overflow:hidden; text-overflow:ellipsis;
    white-space:nowrap; }}
  main {{ max-width:640px; margin:0 auto; padding:36px 28px 80px; }}
  section {{ margin-bottom:36px; }}
  h2 {{ font-family:var(--mono); font-size:11px; letter-spacing:.16em;
    text-transform:uppercase; color:var(--terra); margin-bottom:18px;
    padding-bottom:8px; border-bottom:1px solid var(--hair-strong); }}
  label {{ display:flex; flex-direction:column; gap:5px;
    font-family:var(--mono); font-size:11px; letter-spacing:.08em;
    text-transform:uppercase; color:var(--ink-faint); margin-bottom:14px; }}
  input[type=text], input[type=number], input[type=url] {{
    width:100%; padding:9px 11px; border:1px solid var(--hair-strong);
    background:var(--surface); color:var(--ink); font-family:var(--serif);
    font-size:15px; border-radius:4px; transition:border-color .15s; }}
  input:focus {{ outline:none; border-color:var(--terra); }}
  .row2 {{ display:grid; grid-template-columns:1fr 1fr; gap:0 16px; }}
  .row3 {{ display:grid; grid-template-columns:1fr 1fr 80px; gap:0 16px; }}
  button {{ display:block; width:100%; padding:13px; background:var(--terra);
    color:#fff; font-family:var(--mono); font-size:13px; font-weight:600;
    letter-spacing:.06em; text-transform:uppercase; border:none;
    border-radius:4px; cursor:pointer; transition:background .15s; }}
  button:hover {{ background:var(--burnt); }}
  .notice {{ font-family:var(--mono); font-size:12px; padding:11px 14px;
    border-radius:4px; margin-bottom:24px; }}
  .ok {{ background:#d4edda; color:#1a4731; }}
  .err {{ background:#f8d7da; color:#6b1723; }}
</style>
</head>
<body>
<header>
  <h1>Now Updater</h1>
  <span class="path">{esc(CONFIG_PATH)}</span>
</header>
<main>
{render_notice()}
<form method="POST" action="/">

  <section>
    <h2>Now Reading</h2>
    {field("Title", "r_title", r.get("title",""), placeholder="Book title")}
    {field("Author", "r_author", r.get("author",""), placeholder="Author name")}
    {field("Cover URL", "r_cover", r.get("cover",""), kind="url", placeholder="https://")}
    {field("Note", "r_note", r.get("note",""), placeholder="One-line note")}
    <div class="row2">
      {field("Started", "r_started", r.get("started",""), placeholder="Feb 22")}
      {field("Progress %", "r_progress", r.get("progress",""), kind="number", placeholder="0–100")}
    </div>
  </section>

  <section>
    <h2>Now Playing</h2>
    {field("Title", "p_title", p.get("title",""), placeholder="Game title")}
    <div class="row3">
      {field("Platform", "p_platform", p.get("platform",""), placeholder="PS5")}
      {field("Tag", "p_tag", p.get("tag",""), placeholder="co-op")}
      {field("Hours in", "p_hours", p.get("hours",""), kind="number", placeholder="0")}
    </div>
    {field("Art URL", "p_art", p.get("art",""), kind="url", placeholder="https://")}
    {field("Steam URL", "p_steam", p.get("steam",""), kind="url", placeholder="https://store.steampowered.com/app/...")}
    {field("Note", "p_note", p.get("note",""), placeholder="One-line note")}
  </section>

  <section>
    <h2>Lately</h2>
    {field("Title", "a_title", a.get("title",""), placeholder="e.g. Pigeons")}
    {field("Meta", "a_meta", a.get("meta",""), placeholder="e.g. always pigeons")}
  </section>

  <button type="submit">Save to config.json</button>
</form>
</main>
</body>
</html>"""


_notice = ""


def render_notice():
    global _notice
    n = _notice
    _notice = ""
    return n


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # suppress access log

    def send_page(self, html, status=200):
        body = html.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if urlparse(self.path).path != "/":
            self.send_response(404)
            self.end_headers()
            return
        cfg = load_config()
        self.send_page(render_form(cfg))

    def do_POST(self):
        global _notice
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode()
        data = {k: v[0] for k, v in parse_qs(raw, keep_blank_values=True).items()}

        try:
            cfg = load_config()
            now = cfg.setdefault("params", {}).setdefault("now", {})

            def str_or_none(key):
                v = data.get(key, "").strip()
                return v if v else None

            def int_or_none(key):
                v = data.get(key, "").strip()
                try:
                    return int(v) if v else None
                except ValueError:
                    return None

            reading = {}
            for k, fn in [("title", str_or_none), ("author", str_or_none),
                           ("cover", str_or_none), ("note", str_or_none),
                           ("started", str_or_none)]:
                v = fn(f"r_{k}")
                if v is not None:
                    reading[k] = v
            prog = int_or_none("r_progress")
            if prog is not None:
                reading["progress"] = prog
            now["reading"] = reading

            playing = {}
            for k, fn in [("title", str_or_none), ("platform", str_or_none),
                           ("tag", str_or_none), ("art", str_or_none),
                           ("steam", str_or_none), ("note", str_or_none)]:
                v = fn(f"p_{k}")
                if v is not None:
                    playing[k] = v
            hrs = int_or_none("p_hours")
            if hrs is not None:
                playing["hours"] = hrs
            now["playing"] = playing

            activity = {}
            for k in ("title", "meta"):
                v = str_or_none(f"a_{k}")
                if v is not None:
                    activity[k] = v
            now["activity"] = activity

            save_config(cfg)
            _notice = '<div class="notice ok">Saved to config.json.</div>'
        except Exception as e:
            _notice = f'<div class="notice err">Error: {esc(str(e))}</div>'

        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()


if __name__ == "__main__":
    if not os.path.exists(CONFIG_PATH):
        print(f"Error: config.json not found at {CONFIG_PATH}", file=sys.stderr)
        sys.exit(1)
    print(f"Bricolage Now Updater → http://localhost:{PORT}/")
    print(f"Config: {CONFIG_PATH}")
    print("Ctrl-C to stop.")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
