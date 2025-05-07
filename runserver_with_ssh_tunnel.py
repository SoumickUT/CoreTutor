import os
import sys
from sshtunnel import SSHTunnelForwarder

# Add your project root directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Set DJANGO_SETTINGS_MODULE
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django
django.setup()

from django.core.management import execute_from_command_line

# SSH + MySQL credentials
SSH_HOST = 'host47.registrar-servers.com'
SSH_PORT = 21098
SSH_USER = 'uitsonline'
SSH_PASSWORD = 'ULTDctg2029*&'  # Replace with your real password

MYSQL_HOST = '127.0.0.1'
MYSQL_PORT = 3306

LOCAL_BIND_HOST = '127.0.0.1'
LOCAL_BIND_PORT = 3307  # Local port to bind to avoid conflict

with SSHTunnelForwarder(
    (SSH_HOST, SSH_PORT),
    ssh_username=SSH_USER,
    ssh_password=SSH_PASSWORD,
    remote_bind_address=(MYSQL_HOST, MYSQL_PORT),
    local_bind_address=(LOCAL_BIND_HOST, LOCAL_BIND_PORT)
) as tunnel:
    print(f"SSH Tunnel open on port {LOCAL_BIND_PORT} -> {MYSQL_PORT}")

    # Update Django settings DB HOST to use local tunnel
    from django.conf import settings
    settings.DATABASES['default']['HOST'] = LOCAL_BIND_HOST
    settings.DATABASES['default']['PORT'] = str(LOCAL_BIND_PORT)

    # Run Django command
    execute_from_command_line(sys.argv)