"""A tiny local control panel for the daily run: one Start/Stop button and the last run's time.

    .venv/Scripts/python ui.py        (Windows: or double-click start_ui.bat)
    .venv/bin/python ui.py            (macOS / Linux: or ./start_ui.sh)

Serves http://127.0.0.1:8765 and opens it in the browser. Nothing is reachable from other PCs.
The run is the same as run_daily.bat: fetch + triage, then Claude does /daily-run (when the
`claude` command line is installed; otherwise it tells you to type /daily-run in the app).
"""
import datetime as dt
import json
import os
import signal
import shutil
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WINDOWS = os.name == "nt"
PYTHON = ROOT / ".venv" / ("Scripts/python.exe" if WINDOWS else "bin/python")
LOG_DIR = ROOT / "data" / "logs"
HISTORY = LOG_DIR / "ui_runs.json"
PORT = 8765

lock = threading.Lock()
run = {"proc": None, "log": [], "started": None, "stopped": False, "output_at": None}


def load_history():
    try:
        return json.loads(HISTORY.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def save_history(entry):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    history = (load_history() + [entry])[-50:]
    HISTORY.write_text(json.dumps(history, indent=1), encoding="utf-8")


def find_claude():
    found = shutil.which("claude")
    if found:
        return found
    local = Path.home() / ".local" / "bin" / ("claude.exe" if WINDOWS else "claude")
    return str(local) if local.exists() else None


def emit(line):
    run["output_at"] = dt.datetime.now().timestamp()
    run["log"].append(line.rstrip())
    del run["log"][:-400]


def stream(cmd, label):
    """Run one step, copying its output into the log. Returns the exit code."""
    emit(f"=== {label} ===")
    env = dict(os.environ, PYTHONUTF8="1")
    proc = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace",
                            start_new_session=not WINDOWS)  # own process group, so Stop can end it
    run["proc"] = proc
    for line in proc.stdout:
        emit(line)
    return proc.wait()


def worker(fresh):
    py = str(PYTHON)
    steps = ([([py, "-m", "jobsearch", "fetch", "--again"], "1/3 Fetch new jobs (20-40 min)"),
              ([py, "-m", "jobsearch", "triage"], "2/3 Filter and rank")] if fresh else
             [([py, "-m", "jobsearch", "daily"], "1/2 Fetch (skipped if done today) + triage")])
    result = "finished"
    for cmd, label in steps:
        if run["stopped"]:
            break
        if stream(cmd, label) != 0 and not run["stopped"]:
            result = "failed"
            break
    if result == "finished" and not run["stopped"]:
        claude = find_claude()
        if claude:
            code = stream([claude, "-p", "/daily-run"], "Claude: choose jobs, write letters, build tracker")
            if code != 0 and not run["stopped"]:
                result = "failed"
        else:
            emit("Claude command line not found. Open this folder in the Claude desktop app "
                 "(Code tab) and type /daily-run to finish.")
            result = "jobs fetched and ranked - now type /daily-run in Claude (Code tab)"
    if run["stopped"]:
        result = "stopped"
    with lock:
        save_history({"started": run["started"], "ended": dt.datetime.now().isoformat(timespec="seconds"),
                      "result": result})
        run["proc"] = None


def start(fresh):
    with lock:
        if run["proc"] is not None or (run.get("thread") and run["thread"].is_alive()):
            return
        run.update(log=[], stopped=False, started=dt.datetime.now().isoformat(timespec="seconds"))
        run["thread"] = threading.Thread(target=worker, args=(fresh,), daemon=True)
        run["thread"].start()


def stop():
    run["stopped"] = True
    proc = run["proc"]
    if proc and proc.poll() is None:  # kill the whole tree: Claude and Python start children
        if WINDOWS:
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
        else:
            os.killpg(proc.pid, signal.SIGTERM)


def state():
    running = bool(run.get("thread") and run["thread"].is_alive())
    history = load_history()
    return {"running": running, "started": run["started"] if running else None,
            "quiet": round(dt.datetime.now().timestamp() - run["output_at"]) if running and run["output_at"] else 0,
            "last": history[-1] if history else None, "log": run["log"][-60:]}


PAGE = """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Daily Job Search</title>
<style>
:root{--bg:#f6f7f9;--fg:#1c2230;--card:#fff;--mut:#6b7385;--ok:#1f8a4c;--bad:#c0392b;--acc:#2456d6}
@media(prefers-color-scheme:dark){:root{--bg:#14171f;--fg:#e8ebf2;--card:#1d222d;--mut:#98a1b5;--acc:#5b84f0}}
body{margin:0;background:var(--bg);color:var(--fg);font:16px system-ui,sans-serif;display:grid;place-items:start center;padding:32px 16px}
main{width:100%;max-width:640px;background:var(--card);border-radius:14px;padding:28px;box-shadow:0 2px 12px #0002}
h1{margin:0 0 4px;font-size:22px}.mut{color:var(--mut);font-size:14px}
button{margin:22px 0 8px;width:100%;padding:18px;font-size:18px;font-weight:600;border:0;border-radius:10px;color:#fff;background:var(--acc);cursor:pointer}
button.stop{background:var(--bad)}label{font-size:14px;color:var(--mut)}
.last{margin-top:18px;padding:14px;border-radius:10px;background:var(--bg)}
.last b{font-size:20px;display:block;margin-top:2px}
pre{background:var(--bg);padding:12px;border-radius:10px;font-size:12px;max-height:280px;overflow:auto;white-space:pre-wrap}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;background:var(--mut)}
.on .dot{background:var(--ok);animation:p 1s infinite alternate}@keyframes p{to{opacity:.3}}
</style>
<main><h1>Daily Job Search</h1>
<div id="status" class="mut"><span class="dot"></span><span id="st">Idle</span></div>
<button id="btn">Start daily run</button>
<label><input type="checkbox" id="fresh"> Fetch fresh jobs even if today's fetch is already done</label>
<div class="last"><span class="mut">Previous run</span><b id="last">-</b><span class="mut" id="res"></span></div>
<h3 class="mut">Progress</h3><pre id="log">Nothing running.</pre></main>
<script>
const $=id=>document.getElementById(id);let running=false;
const fmt=s=>s?new Date(s).toLocaleString([],{dateStyle:'full',timeStyle:'short'}):null;
async function tick(){
  let s;
  try{s=await (await fetch('/state')).json()}catch(e){
    $('st').textContent='Panel stopped - close this tab and start the panel again';$('btn').disabled=true;return}
  $('btn').disabled=false;running=s.running;
  $('status').className='mut'+(running?' on':'');
  $('st').textContent=running?'Running since '+new Date(s.started).toLocaleTimeString([],{timeStyle:'short'})+(s.quiet>120?' - no new output for '+Math.round(s.quiet/60)+' min (the fetch is slow, or the PC went to sleep)':''):'Idle';
  $('btn').textContent=running?'Stop':'Start daily run';$('btn').className=running?'stop':'';
  $('fresh').disabled=running;
  $('last').textContent=s.last?fmt(s.last.started):'No run yet';
  $('res').textContent=s.last?'Result: '+s.last.result+' (ended '+new Date(s.last.ended).toLocaleTimeString([],{timeStyle:'short'})+')':'';
  if(s.log.length||running){$('log').textContent=s.log.join('\\n')||'Starting...';}
}
$('btn').onclick=async()=>{await fetch(running?'/stop':'/start?fresh='+($('fresh').checked?1:0),{method:'POST'});tick()};
tick();setInterval(tick,2000);
</script></html>"""


class Server(ThreadingHTTPServer):
    allow_reuse_address = False  # on Windows reuse lets two copies share the port and split the clicks


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, body, kind="application/json"):
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", kind + "; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/state":
            self.reply(json.dumps(state()))
        else:
            self.reply(PAGE, "text/html")

    def do_POST(self):
        if self.path.startswith("/start"):
            start("fresh=1" in self.path)
        elif self.path == "/stop":
            stop()
        self.reply("{}")


def free_port():
    if not WINDOWS:  # only Windows lets a second copy share the port
        return
    out = subprocess.run(["netstat", "-ano", "-p", "TCP"], capture_output=True, text=True).stdout
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[1].endswith(f":{PORT}") and parts[3] == "LISTENING":
            subprocess.run(["taskkill", "/PID", parts[4], "/T", "/F"], capture_output=True)
    threading.Event().wait(1)


def main():
    if not PYTHON.exists():
        print("Run setup first (setup.bat on Windows, ./setup.sh on macOS / Linux).")
        return 1
    try:
        server = Server(("127.0.0.1", PORT), Handler)
    except OSError:
        # An older copy of the panel is still running (possibly a buggy one): replace it
        free_port()
        try:
            server = Server(("127.0.0.1", PORT), Handler)
        except OSError:
            print(f"Port {PORT} is busy with another program. Close it and try again.")
            return 1
    print(f"Daily Job Search panel: http://127.0.0.1:{PORT}  (close this window to quit)")
    threading.Timer(0.8, webbrowser.open, args=(f"http://127.0.0.1:{PORT}",)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
