"""Notification callbacks used by Airflow DAGs."""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)


def notify_failure(context: dict) -> None:
    """Log structured context when a DAG task fails."""
    dag_id = context["dag"].dag_id
    task_id = context["task_instance"].task_id
    run_id = context["run_id"]
    log_url = context["task_instance"].log_url
    exception = context.get("exception", "n/a")

    log.error(
        "TASK FAILED | dag=%s | task=%s | run_id=%s | exception=%s | logs=%s",
        dag_id,
        task_id,
        run_id,
        exception,
        log_url,
    )
