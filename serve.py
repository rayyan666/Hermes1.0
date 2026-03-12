import sys
import os
import platform
import threading

IS_WINDOWS = platform.system() == "Windows"
PORT = int(os.getenv("PORT", 5000))


def run_waitress(app):
    from waitress import serve
    print(f"[serve] Waitress running on http://0.0.0.0:{PORT}")
    serve(app, host="0.0.0.0", port=PORT, threads=4)


def run_gunicorn(app):
    from gunicorn.app.base import BaseApplication

    class StandaloneApp(BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()

        def load_config(self):
            for key, value in self.options.items():
                self.cfg.set(key.lower(), value)

        def load(self):
            return self.application

    options = {
        "bind": f"0.0.0.0:{PORT}",
        "workers": 2,
        "threads": 2,
        "worker_class": "gthread",
        "timeout": 120,
        "loglevel": "info",
    }
    print(f"[serve] Gunicorn running on http://0.0.0.0:{PORT}")
    StandaloneApp(app, options).run()


def run_flask_dev(app):
    print(f"[serve] Flask dev server on http://localhost:{PORT} (debug=True)")
    app.run(host="0.0.0.0", port=PORT, debug=True, use_reloader=False)


if __name__ == "__main__":
    from main import app, mcp

    mode = next((a for a in sys.argv[1:] if a.startswith("--")), "")

    if mode == "--dev":
        run_flask_dev(app)

    elif mode == "--mcp":
        print("[serve] MCP stdio mode — starting Flask in background thread...")
        server_fn = run_waitress if IS_WINDOWS else run_gunicorn
        threading.Thread(target=server_fn, args=(app,), daemon=True).start()
        print("[serve] Starting MCP server on stdio transport...")
        mcp.run(transport="stdio")

    else:
        # Default: HTTP server only
        if IS_WINDOWS:
            run_waitress(app)
        else:
            run_gunicorn(app)
