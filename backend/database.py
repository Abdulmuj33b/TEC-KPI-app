import psycopg
from psycopg.rows import dict_row

from config import settings


def get_connection():
    return psycopg.connect(
        settings.database_url,
        connect_timeout=5,
        row_factory=dict_row,
    )