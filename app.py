from gevent import monkey
monkey.patch_all()

import os
import time
from flask import Flask, render_template, Response
from markupsafe import Markup
from flask_socketio import SocketIO
import markdown
from mycharts.pnl_chart import generate_pnl_chart

app = Flask(__name__)
socketio = SocketIO(
    app, 
    async_mode='gevent', 
    cors_allowed_origins="*", 
    logger=False, 
    engineio_logger=False
)

PAGES_DIR = "pages"

@app.route("/")
def index():
    pages = [f.replace(".html", "").replace("_", " ") for f in os.listdir(PAGES_DIR) if f.endswith(".html")]
    return render_template("base.html", pages=pages, content="<h2>Select a page</h2>")

@app.route("/page/<name>")
def page(name):
    filename = f"{name.replace(' ', '_')}.html"
    path = os.path.join(PAGES_DIR, filename)
    with open(path) as f:
        html = f.read()
    pages = [f.replace(".html", "").replace("_", " ") for f in os.listdir(PAGES_DIR) if f.endswith(".html")]
    return render_template("base.html", content=Markup(html), pages=pages, page=name)

@app.route("/chart")
def chart():
    pages = [f.replace(".html", "").replace("_", " ") for f in os.listdir(PAGES_DIR) if f.endswith(".html")]
    chart_html = generate_pnl_chart()
    return render_template("base.html", pages=pages, content=Markup(chart_html))

# Gevent-safe background task for file watching
def watch_files():
    last_mtimes = {}
    while True:
        if os.path.exists(PAGES_DIR):
            for filename in os.listdir(PAGES_DIR):
                if not filename.endswith(".html"):
                    continue

                path = os.path.join(PAGES_DIR, filename)
                mtime = os.path.getmtime(path)

                if filename not in last_mtimes:
                    last_mtimes[filename] = mtime
                elif mtime != last_mtimes[filename]:
                    last_mtimes[filename] = mtime
                    socketio.emit("file_changed", {"page": filename})
        
        # Use socketio.sleep instead of time.sleep to yield control to Gevent
        socketio.sleep(2)

# Start background task safely when server launches
@socketio.on('connect')
def handle_connect():
    global watcher_started
    if not getattr(app, 'watcher_started', False):
        socketio.start_background_task(watch_files)
        app.watcher_started = True

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
