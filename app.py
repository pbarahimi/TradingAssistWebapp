from flask import Flask, render_template
from markupsafe import Markup
from gevent import monkey
from flask_socketio import SocketIO
import markdown
import os
import time
import threading
from flask import Response

from mycharts.pnl_chart import generate_pnl_chart

app = Flask(__name__)
monkey.patch_all()
socketio = SocketIO(app, async_mode='gevent', logger=True, engineio_logger=True) #cors_allowed_origins="*")

PAGES_DIR = "pages"
clients = []

def render_md(filename):
    path = os.path.join(PAGES_DIR, filename)
    print(path)
    if not os.path.exists(path):
        return "<h1>Page not found</h1>"
    with open(path, "r", encoding="utf-8") as f:
        md = f.read()
    return markdown.markdown(md, extensions=["fenced_code", "tables"])

def render_html(filename):
    path = os.path.join(PAGES_DIR, filename)
    with open(path) as f:
        html = f.read()
    return html
    
@app.route("/")
def index():
    pages = [f.replace(".html", "").replace("_", " ") for f in os.listdir(PAGES_DIR) if f.endswith(".html")]
    return render_template("base.html", pages=pages, content="<h2>Select a page</h2>")

@app.route("/page/<name>")
def page(name):
    filename = f"{name.replace(" ", "_")}.html"
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

def watch_files():
    last_mtimes = {}

    while True:
        # print('Testing for file changes')
        for filename in os.listdir(PAGES_DIR):
            if not filename.endswith(".html"):
                continue

            path = os.path.join(PAGES_DIR, filename)
            mtime = os.path.getmtime(path)

            if filename not in last_mtimes:
                last_mtimes[filename] = mtime
            elif mtime != last_mtimes[filename]:
                last_mtimes[filename] = mtime

                # Notify browser that THIS file changed
                socketio.emit("file_changed", {"page": filename})
        time.sleep(2)


if __name__ == "__main__":
    threading.Thread(target=watch_files, daemon=True).start()
    socketio.run(app,
                 host="0.0.0.0",
                 port=5000,
                 debug=False
                )
