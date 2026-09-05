"""Small shared helpers for auditable PostgreSQL ingestion jobs."""

from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import dataclass


LOG = logging.getLogger("regrove.ingestion")


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: str
    database: str
    user: str
    psql: str

    @classmethod
    def from_environment(cls) -> "DatabaseConfig":
        return cls(
            host=os.getenv("PGHOST", "localhost"),
            port=os.getenv("PGPORT", os.getenv("REGROVE_DB_PORT", "5433")),
            database=os.getenv("PGDATABASE", os.getenv("POSTGRES_DB", "regrove")),
            user=os.getenv("PGUSER", os.getenv("POSTGRES_USER", "regrove")),
            psql=os.getenv("PSQL", "psql"),
        )

    def environment(self) -> dict[str, str]:
        env = os.environ.copy()
        env.update(
            PGHOST=self.host,
            PGPORT=self.port,
            PGDATABASE=self.database,
            PGUSER=self.user,
        )
        return env


def run_psql(
    config: DatabaseConfig,
    sql: str,
    *,
    variables: dict[str, object] | None = None,
) -> str:
    """Run SQL with stop-on-error semantics; an open transaction rolls back on failure."""
    command = [
        config.psql,
        "-X",
        "-qAt",
        "-v",
        "ON_ERROR_STOP=1",
    ]
    for name, value in (variables or {}).items():
        command.extend(("-v", f"{name}={value}"))

    completed = subprocess.run(
        command,
        input=sql,
        text=True,
        capture_output=True,
        env=config.environment(),
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "psql failed without an error message")
    return completed.stdout.strip()


def register_source(config: DatabaseConfig, source: dict[str, str]) -> int:
    result = run_psql(
        config,
        """
        INSERT INTO source (source_name, provider, url, licence, version)
        VALUES (:'name', :'provider', :'url', :'licence', :'version')
        ON CONFLICT (source_name, version) DO UPDATE SET
            provider = EXCLUDED.provider,
            url = EXCLUDED.url,
            licence = EXCLUDED.licence
        RETURNING source_id;
        """,
        variables=source,
    )
    return int(result.splitlines()[-1])


def start_data_load(config: DatabaseConfig, source_id: int, notes: str) -> int:
    result = run_psql(
        config,
        """
        INSERT INTO data_load (source_id, status, notes)
        VALUES (:source_id, 'running', :'notes')
        RETURNING load_id;
        """,
        variables={"source_id": source_id, "notes": notes},
    )
    return int(result.splitlines()[-1])


def finish_data_load(
    config: DatabaseConfig,
    load_id: int,
    *,
    status: str,
    received: int | None,
    accepted: int | None,
    rejected: int | None,
    notes: str,
) -> None:
    values = {
        "load_id": load_id,
        "status": status,
        "received": "" if received is None else received,
        "accepted": "" if accepted is None else accepted,
        "rejected": "" if rejected is None else rejected,
        "notes": notes[:4000],
    }
    run_psql(
        config,
        """
        UPDATE data_load
        SET completed_at = now(),
            status = :'status',
            rows_received = NULLIF(:'received', '')::integer,
            rows_accepted = NULLIF(:'accepted', '')::integer,
            rows_rejected = NULLIF(:'rejected', '')::integer,
            notes = :'notes'
        WHERE load_id = :load_id;
        """,
        variables=values,
    )


def configure_logging(verbose: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )
