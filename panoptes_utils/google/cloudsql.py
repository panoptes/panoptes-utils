import os

import psycopg2
from psycopg2.extras import RealDictCursor

from panoptes_utils import error


def get_db_proxy_conn(
        host='127.0.0.1',
        port=5432,
        db_name='panoptes',
        db_user='panoptes',
        db_pass=None,
        **kwargs):
    """Return postgres connection to local proxy.

    Note:
        The proxy must be started and authenticated to the appropriate instance
        before this function will work. See `$POCS/scripts/connect_clouddb_proxy.py`.

    Args:
        host (str, optional): Hostname, default localhost.
        port (str, optional): Port, default 5432.
        db_user (str, optional): Name of db user, default 'panoptes'.
        db_name (str, optional): Name of db, default 'postgres'.
        db_pass (str, optional): Password for given db and user, defaults to
            $PG_PASSWORD or None if not set.

    Returns:
        `psycopg2.Connection`: DB connection object.
    """
    if db_pass is None:
        db_pass = os.getenv('PGPASSWORD')

    conn_params = {
        'host': host,
        'port': port,
        'user': db_user,
        'dbname': db_name,
    }

    try:
        conn = psycopg2.connect(**conn_params)
    except psycopg2.OperationalError as e:
        raise error.GoogleCloudError("Can't connect to cloud db "
                                     "Make sure the cloud sql proxy is running. {}".format(e)
                                     )

    return conn


def get_cursor(**kwargs):
    """Get a Cursor object.

    Args:
        **kwargs: Passed to `get_db_prox_conn`

    Returns:
        `psycopg2.Cursor`: Cursor object.
    """
    conn = get_db_proxy_conn(**kwargs)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    return cur
