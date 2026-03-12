"""
Run: gunicorn -c gunicorn.conf.py main:app
"""

import os

# Server
bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"
workers = 2          # 2 * CPU cores + 1 is typical; keep low for local use
threads = 2          # threads per worker
worker_class = "gthread"
timeout = 120        # seconds before killing a worker (Groq calls can be slow)
keepalive = 5

# Logging
accesslog = "-"      # stdout
errorlog  = "-"      # stdout
loglevel  = "info"
access_log_format = '%(h)s "%(r)s" %(s)s %(b)s %(D)sµs'

# Reload on code change (dev only — remove for production)
reload = os.getenv("GUNICORN_RELOAD", "false").lower() == "true"