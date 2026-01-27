import os

timeout = 300
graceful_timeout = 300
workers = int(os.environ.get("WEB_CONCURRENCY", "2"))
worker_class = "sync"
worker_connections = 1000
accesslog = "-"
errorlog = "-"
loglevel = "info"
keepalive = 120
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
