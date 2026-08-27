from flask import Flask, render_template
from markupsafe import Markup
import markdown
import os

from mycharts.pnl_chart import generate_pnl_chart

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from flask import Response

app = Flask(__name__)

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

@app.route("/")
def index():
    pages = [f.replace(".md", "").replace("_", " ") for f in os.listdir(PAGES_DIR) if f.endswith(".md")]
    return render_template("base.html", pages=pages, content="<h2>Select a page</h2>")

@app.route("/page/<name>")
def page(name):
    filename = f"{name.replace(" ", "_")}.md"
    html = render_md(filename)
    pages = [f.replace(".md", "").replace("_", " ") for f in os.listdir(PAGES_DIR) if f.endswith(".md")]
    return render_template("base.html", pages=pages, content=Markup(html))

@app.route("/chart")
def chart():
    pages = [f.replace(".md", "").replace("_", " ") for f in os.listdir(PAGES_DIR) if f.endswith(".md")]
    chart_html = generate_pnl_chart()
    return render_template("base.html", pages=pages, content=Markup(chart_html))

# --- Live Reload (SSE) ---
class ChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        for q in clients:
            q.put("reload")

@app.route("/events")
def events():
    def stream():
        from queue import Queue
        q = Queue()
        clients.append(q)
        try:
            while True:
                msg = q.get()
                yield f"data: {msg}\n\n"
        finally:
            clients.remove(q)
    return Response(stream(), mimetype="text/event-stream")

observer = Observer()
observer.schedule(ChangeHandler(), path=PAGES_DIR, recursive=True)
observer.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
