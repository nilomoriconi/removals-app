# Gunicorn configuration file
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
# bind = "127.0.0.1:8000"  # Alternative: bind to port instead of socket

# Worker processes
workers = 3
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 2

# Logging
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = 'info'

# Process naming
proc_name = 'removals_app'

# SSL (if not using Nginx)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile' 