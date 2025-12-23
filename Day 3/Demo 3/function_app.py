import json
import logging
import os
import time
from typing import Any, Dict, Iterable

import azure.functions as func
import psycopg2
from psycopg2 import OperationalError, errors

from retry_policy import RetryPolicyBuilder

RETRYABLE_ERRORS: Iterable[type[BaseException]] = (
    OperationalError,
    errors.SerializationFailure,
    errors.DeadlockDetected,
    errors.ConnectionException,
    errors.AdminShutdown,
)

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
retry_builder = RetryPolicyBuilder(app)
host_retry_enabled = retry_builder.enabled
http_route = retry_builder.http_route

def _connection_params() -> Dict[str, Any]:
    return {
        "host": os.environ["PG_HOST"],
        "database": os.environ["PG_DB"],
        "user": os.environ["PG_USER"],
        "password": os.environ["PG_PASSWORD"],
        "port": os.environ.get("PG_PORT", "5432"),
        "sslmode": os.environ.get("PG_SSLMODE", "require"),
        "connect_timeout": int(os.getenv("PG_CONNECT_TIMEOUT", "10")),
    }


def execute_with_retry(operation):
    """Wrap a database action with exponential backoff retries."""

    max_attempts = int(os.getenv("PG_ACTION_MAX_ATTEMPTS", "4"))
    base_delay = float(os.getenv("PG_ACTION_BASE_DELAY_SECONDS", "1.5"))
    cap_delay = float(os.getenv("PG_ACTION_MAX_DELAY_SECONDS", "15"))
    attempt = 0

    while attempt < max_attempts:
        attempt += 1
        try:
            operation()
            return attempt
        except RETRYABLE_ERRORS as exc:
            if attempt >= max_attempts:
                logging.error("Retry attempts exhausted for PostgreSQL action.")
                raise

            sleep_for = min(base_delay * (2 ** (attempt - 1)), cap_delay)
            logging.warning(
                "Transient PostgreSQL error '%s' (attempt %s/%s). "
                "Retrying in %.1f seconds.",
                exc,
                attempt,
                max_attempts,
                sleep_for,
            )
            time.sleep(sleep_for)


def insert_records(records, simulate_transient_errors: int) -> None:
    """Insert rows into PostgreSQL, optionally simulating transient failures."""

    fault_tracker = {"count": 0}

    def operation():
        if fault_tracker["count"] < simulate_transient_errors:
            fault_tracker["count"] += 1
            raise OperationalError("Simulated transient connection reset.")

        conn = psycopg2.connect(**_connection_params())

        try:
            with conn:
                with conn.cursor() as cursor:
                    for record in records:
                        if "email" not in record:
                            raise ValueError("Each record must include an email field.")

                        cursor.execute(
                            """
                            INSERT INTO logicapp.retry_messages (email, payload, created_at)
                            VALUES (%s, %s, NOW())
                            """,
                            (record["email"], json.dumps(record)),
                        )
        finally:
            conn.close()

    attempts = execute_with_retry(operation)
    return attempts


def _parse_request_payload(req: func.HttpRequest):
    try:
        body = req.get_json()
    except ValueError:
        return None, None, func.HttpResponse(
            json.dumps({"error": "Invalid JSON payload."}),
            status_code=400,
            mimetype="application/json",
        )

    records = body.get("records", [])
    if not isinstance(records, list) or not records:
        return None, None, func.HttpResponse(
            json.dumps({"error": "Body must include a non-empty 'records' array."}),
            status_code=400,
            mimetype="application/json",
        )

    simulate_raw = body.get("simulateTransientErrors", 0)
    try:
        simulate_transient_errors = int(simulate_raw)
        if simulate_transient_errors < 0:
            raise ValueError
    except (ValueError, TypeError):
        return None, None, func.HttpResponse(
            json.dumps(
                {
                    "error": "simulateTransientErrors must be a non-negative integer "
                    "if provided."
                }
            ),
            status_code=400,
            mimetype="application/json",
        )

    return records, simulate_transient_errors, None


def _handle_pg_retry(req: func.HttpRequest, mode: str) -> func.HttpResponse:
    records, simulate_transient_errors, error_response = _parse_request_payload(req)
    if error_response:
        return error_response

    try:
        db_attempts = insert_records(records, simulate_transient_errors)

        response = {
            "status": "success",
            "inserted": len(records),
            "dbAttempts": db_attempts,
            "hostRetryConfigured": host_retry_enabled,
            "mode": mode,
        }
        return func.HttpResponse(
            json.dumps(response),
            status_code=200,
            mimetype="application/json",
        )

    except RETRYABLE_ERRORS as exc:
        logging.error("PostgreSQL action kept failing: %s", exc)
        raise  # triggers Azure Functions host-level retry

    except Exception as exc:
        logging.error("Non-retryable failure: %s", exc)
        return func.HttpResponse(
            json.dumps({"status": "failed", "error": str(exc)}),
            status_code=500,
            mimetype="application/json",
        )


@app.function_name(name="pg-retry-demo")
@http_route("pg-retry-demo", methods=["POST"])
def pg_retry_demo(req: func.HttpRequest) -> func.HttpResponse:
    return _handle_pg_retry(req, mode="single")


@app.function_name(name="pg-retry-demo-bulk")
@http_route("pg-retry-demo-bulk", methods=["POST"])
def pg_retry_demo_bulk(req: func.HttpRequest) -> func.HttpResponse:
    return _handle_pg_retry(req, mode="bulk")
