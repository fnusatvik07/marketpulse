"""Checkpointer factory: WHERE the agent's memory lives.

This file answers one question: which database stores the checkpoints?

  - Postgres  (normal case)  enterprise-grade, survives restarts, scales
  - SQLite    (fallback)     a local file, used only if Postgres is down

Both classes implement the same BaseCheckpointSaver interface, which is
why graph.py can stay completely ignorant of this choice. Swapping to
Redis, MongoDB or CosmosDB would be the same one-line change here.
"""
import logging
import sqlite3

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.sqlite import SqliteSaver
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from . import config

logger = logging.getLogger(__name__)

# The pool retries in the background and logs every failed attempt, which
# floods the terminal when Postgres is down. We fail fast below instead.
logging.getLogger("psycopg.pool").setLevel(logging.CRITICAL)


def get_checkpointer():
    """Return a ready-to-use checkpointer. Tries Postgres first."""
    try:
        # A connection POOL, not a single connection: the API serves many
        # requests concurrently and each one needs a connection briefly.
        pool = ConnectionPool(
            conninfo=config.POSTGRES_URI,
            max_size=10,
            open=False,
            kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
        )
        # Try to connect for 5 seconds, then give up and fall back,
        # instead of retrying forever with a wall of error logs.
        pool.open(wait=True, timeout=5)
        checkpointer = PostgresSaver(pool)

        # setup() creates the checkpoint tables. It only does real work the
        # very first time; afterwards it is a no-op. Forgetting this line is
        # the #1 PostgresSaver beginner error.
        checkpointer.setup()
        logger.info("using PostgresSaver")
        return checkpointer
    except Exception as exc:
        logger.warning("Postgres unavailable (%s), falling back to SQLite", exc)
        conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
        return SqliteSaver(conn)


def list_threads(checkpointer) -> list[str]:
    """Every conversation that exists, straight from the checkpoints table.

    Worth showing in class: checkpoints are ordinary database rows. Plain
    SQL works on them, which means backups, replication and dashboards all
    come for free.
    """
    sql = "SELECT DISTINCT thread_id FROM checkpoints ORDER BY thread_id"
    if isinstance(checkpointer, PostgresSaver):
        with checkpointer.conn.connection() as conn:
            rows = conn.execute(sql).fetchall()
        return [r["thread_id"] if isinstance(r, dict) else r[0] for r in rows]
    rows = checkpointer.conn.execute(sql).fetchall()
    return [r[0] for r in rows]
