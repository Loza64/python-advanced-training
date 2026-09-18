"""Constantes compartidas entre seeders y servicios.

Se centralizan aquí los nombres de los roles de sistema para evitar
strings mágicos repetidos en seed.py, role_service.py y user_service.py.
"""

SUPER_ADMIN_ROLE_NAME = "super_admin"
ADMIN_ROLE_NAME = "admin"
CLIENT_ROLE_NAME = "client"

SYSTEM_ROLE_NAMES = {SUPER_ADMIN_ROLE_NAME, ADMIN_ROLE_NAME, CLIENT_ROLE_NAME}
