#!/usr/bin/env python3
"""
Bricolage Now Updater
Serves a local form at http://localhost:8787

On Save:
  1. Writes data/now.json in the theme repo
  2. git commit + push
  3. POSTs a Micropub note to micro.blog → triggers site rebuild

Usage:
    python3 now-updater.py            # theme root inferred from script location
    python3 now-updater.py /path/to/theme-root
"""

import json, os, subprocess, sys, urllib.request, urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

PORT = 8787
THEME_ROOT = os.path.dirname(os.path.abspath(__file__))
if len(sys.argv) > 1:
    THEME_ROOT = os.path.abspath(sys.argv[1])

NOW_PATH    = os.path.join(THEME_ROOT, "data", "now.json")
TOKEN_PATH  = os.path.join(THEME_ROOT, ".now-token")   # gitignored
MICROPUB_URL = "https://micro.blog/micropub"


# ── helpers ──────────────────────────────────────────────────────────────────

def load_now():
    if os.path.exists(NOW_PATH):
        with open(NOW_PATH) as f:
            return json.load(f)
    return {}

def save_now(data):
    os.makedirs(os.path.dirname(NOW_PATH), exist_ok=True)
    with open(NOW_PATH, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

def load_token():
    if os.path.exists(TOKEN_PATH):
        return open(TOKEN_PATH).read().strip()
    return ""

def save_token(token):
    with open(TOKEN_PATH, "w") as f:
        f.write(token.strip())

def git_push():
    cmds = [
        ["git", "-C", THEME_ROOT, "add", "data/now.json"],
        ["git", "-C", THEME_ROOT, "commit", "-m", "Update Now panel"],
        ["git", "-C", THEME_ROOT, "push"],
    ]
    for cmd in cmds:
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            if "nothing to commit" in r.stdout + r.stderr:
                continue
            return False, r.stderr.strip() or r.stdout.strip()
    return True, ""

def trigger_rebuild(token):
    payload = json.dumps({
        "type": ["h-entry"],
        "properties": {
            "content": ["Now panel updated"],
            "post-status": ["draft"]
        }
    }).encode()
    req = urllib.request.Request(
        MICROPUB_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    try:
        urllib.request.urlopen(req, timeout=10)
        return True, ""
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        return False, f"HTTP {e.code}: {body[:200]}"
    except Exception as e:
        return False, str(e)

def esc(s):
    return str(s or "").replace("&","&amp;").replace('"',"&quot;").replace("<","&lt;")

def field(label, name, value="", kind="text", placeholder=""):
    val = esc(str(value) if value is not None else "")
    ph  = f' placeholder="{esc(placeholder)}"' if placeholder else ""
    return (f'<label>{label}'
            f'<input type="{kind}" name="{name}" value="{val}"{ph}>'
            f'</label>')


# ── HTML ─────────────────────────────────────────────────────────────────────

STYLE = """
:root{--terra:#b5563a;--burnt:#c2622d;--bg:#f5ede0;--surface:#fbf6ec;
  --ink:#3a3630;--ink-soft:#6b6357;--ink-faint:#9a9183;
  --hair:#e2d7c4;--hair-strong:#d4c6ad;
  --serif:Georgia,"Times New Roman",serif;
  --mono:"JetBrains Mono",ui-monospace,monospace;}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--bg);color:var(--ink);font-family:var(--serif);
  font-size:16px;line-height:1.5;-webkit-font-smoothing:antialiased;}
header{position:sticky;top:0;height:52px;background:var(--bg);
  border-bottom:1px solid var(--hair);display:flex;align-items:center;
  padding:0 28px;gap:14px;}
header::before{content:"";position:absolute;top:0;left:0;right:0;
  height:4px;background:var(--terra);}
header h1{font-size:18px;font-weight:600;color:var(--burnt);}
header .path{font-family:var(--mono);font-size:11px;color:var(--ink-faint);
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
main{max-width:640px;margin:0 auto;padding:36px 28px 80px;}
section{margin-bottom:36px;}
h2{font-family:var(--mono);font-size:11px;letter-spacing:.16em;
  text-transform:uppercase;color:var(--terra);margin-bottom:18px;
  padding-bottom:8px;border-bottom:1px solid var(--hair-strong);}
label{display:flex;flex-direction:column;gap:5px;font-family:var(--mono);
  font-size:11px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--ink-faint);margin-bottom:14px;}
input[type=text],input[type=number],input[type=url],input[type=password]{
  width:100%;padding:9px 11px;border:1px solid var(--hair-strong);
  background:var(--surface);color:var(--ink);font-family:var(--serif);
  font-size:15px;border-radius:4px;transition:border-color .15s;}
input:focus{outline:none;border-color:var(--terra);}
.row2{display:grid;grid-template-columns:1fr 1fr;gap:0 16px;}
.row3{display:grid;grid-template-columns:1fr 1fr 80px;gap:0 16px;}
button{display:block;width:100%;padding:13px;background:var(--terra);
  color:#fff;font-family:var(--mono);font-size:13px;font-weight:600;
  letter-spacing:.06em;text-transform:uppercase;border:none;
  border-radius:4px;cursor:pointer;transition:background .15s;}
button:hover{background:var(--burnt);}
.notice{font-family:var(--mono);font-size:12px;padding:11px 14px;
  border-radius:4px;margin-bottom:24px;}
.ok{background:#d4edda;color:#1a4731;}
.warn{background:#fff3cd;color:#664d03;}
.err{background:#f8d7da;color:#6b1723;}
.steps{font-family:var(--mono);font-size:12px;display:flex;
  flex-direction:column;gap:6px;margin-bottom:24px;}
.step{display:flex;align-items:center;gap:8px;padding:8px 12px;
  border-radius:4px;background:var(--surface);border:1px solid var(--hair);}
.step.ok{border-color:#a3d9b1;background:#eaf7ee;}
.step.err{border-color:#f1b0b7;background:#fdf0f1;}
.step.warn{border-color:#ffd970;background:#fffbec;}
.dot{width:8px;height:8px;border-radius:50%;flex:none;}
.ok .dot{background:#2d7a47;}
.err .dot{background:#b02a37;}
.warn .dot{background:#997404;}
"""

_notice_html = ""

def render_notice():
    global _notice_html
    n = _notice_html
    _notice_html = ""
    return n

def render_form(now, token=""):
    r = now.get("reading", {})
    p = now.get("playing", {})
    a = now.get("activity", {})
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bricolage · Now Updater</title>
<style>{STYLE}</style></head>
<body>
<header>
  <h1>Now Updater</h1>
  <span class="path">{esc(NOW_PATH)}</span>
</header>
<main>
{render_notice()}
<form method="POST" action="/">

  <section>
    <h2>Now Reading</h2>
    {field("Title","r_title",r.get("title",""),placeholder="Book title")}
    {field("Author","r_author",r.get("author",""),placeholder="Author name")}
    {field("Cover URL","r_cover",r.get("cover",""),kind="url",placeholder="https://")}
    {field("Note","r_note",r.get("note",""),placeholder="One-line note")}
    <div class="row2">
      {field("Started","r_started",r.get("started",""),placeholder="Feb 22")}
      {field("Progress %","r_progress",r.get("progress",""),kind="number",placeholder="0–100")}
    </div>
  </section>

  <section>
    <h2>Now Gaming</h2>
    {field("Title","p_title",p.get("title",""),placeholder="Game title")}
    <div class="row3">
      {field("Platform","p_platform",p.get("platform",""),placeholder="Switch")}
      {field("Tag","p_tag",p.get("tag",""),placeholder="co-op")}
      {field("Hours in","p_hours",p.get("hours",""),kind="number",placeholder="0")}
    </div>
    {field("Art URL","p_art",p.get("art",""),kind="url",placeholder="https://")}
    {field("Steam URL","p_steam",p.get("steam",""),kind="url",placeholder="https://store.steampowered.com/app/...")}
    {field("Note","p_note",p.get("note",""),placeholder="One-line note")}
  </section>

  <section>
    <h2>Lately</h2>
    {field("Title","a_title",a.get("title",""),placeholder="e.g. Pigeons")}
    {field("Meta","a_meta",a.get("meta",""),placeholder="e.g. always pigeons")}
  </section>

  <section>
    <h2>Micro.blog Token</h2>
    {field("API Token (saved locally, never committed)","mb_token",token,kind="password",placeholder="paste token to enable auto-rebuild")}
  </section>

  <button type="submit">Save · Push · Rebuild</button>
</form>
</main></body></html>"""


# ── request handler ───────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass

    def send_page(self, html, status=200):
        body = html.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if urlparse(self.path).path != "/":
            self.send_response(404); self.end_headers(); return
        self.send_page(render_form(load_now(), load_token()))

    def do_POST(self):
        global _notice_html
        raw  = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
        data = {k: v[0] for k, v in parse_qs(raw, keep_blank_values=True).items()}

        def s(k): v=data.get(k,"").strip(); return v or None
        def n(k):
            v=data.get(k,"").strip()
            try: return int(v) if v else None
            except ValueError: return None

        steps = []

        # 1 — build and save now.json
        try:
            reading = {k:f(f"r_{k}") for k,f in [
                ("title",s),("author",s),("cover",s),("note",s),("started",s)]}
            reading = {k:v for k,v in reading.items() if v}
            if n("r_progress") is not None: reading["progress"] = n("r_progress")

            playing = {k:f(f"p_{k}") for k,f in [
                ("title",s),("platform",s),("tag",s),("art",s),("steam",s),("note",s)]}
            playing = {k:v for k,v in playing.items() if v}
            if n("p_hours") is not None: playing["hours"] = n("p_hours")

            activity = {k:s(f"a_{k}") for k in ("title","meta")}
            activity = {k:v for k,v in activity.items() if v}

            save_now({"reading":reading,"playing":playing,"activity":activity})
            steps.append(("ok","Saved data/now.json"))
        except Exception as e:
            steps.append(("err", f"Save failed: {esc(str(e))}"))
            _notice_html = self._render_steps(steps)
            self._redirect(); return

        # 2 — save token if provided
        token = data.get("mb_token","").strip()
        if token:
            save_token(token)
        else:
            token = load_token()

        # 3 — git push
        ok, msg = git_push()
        if ok:
            steps.append(("ok","Pushed to GitHub"))
        else:
            steps.append(("err", f"git push failed: {esc(msg)}"))

        # 4 — Micropub rebuild trigger
        if token:
            ok, msg = trigger_rebuild(token)
            if ok:
                steps.append(("ok","Micropub ping sent → rebuild triggered"))
            else:
                steps.append(("warn", f"Micropub ping failed (rebuild manually): {esc(msg)}"))
        else:
            steps.append(("warn","No token — trigger a rebuild manually in Micro.blog"))

        _notice_html = self._render_steps(steps)
        self._redirect()

    def _render_steps(self, steps):
        rows = "".join(
            f'<div class="step {cls}"><span class="dot"></span>{msg}</div>'
            for cls, msg in steps
        )
        return f'<div class="steps">{rows}</div>'

    def _redirect(self):
        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()


# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not os.path.exists(THEME_ROOT):
        print(f"Error: theme root not found: {THEME_ROOT}", file=sys.stderr)
        sys.exit(1)
    print(f"Bricolage Now Updater → http://localhost:{PORT}/")
    print(f"Theme root: {THEME_ROOT}")
    print("Ctrl-C to stop.")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
