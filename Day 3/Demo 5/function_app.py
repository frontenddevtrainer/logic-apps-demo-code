import json
import logging
import os
from typing import Any, Dict, List

import azure.functions as func
import psycopg2
from psycopg2 import Error as PsycopgError

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


def _connection_params() -> Dict[str, Any]:
    return {
        "host": os.environ["PG_HOST"],
        "database": os.environ["PG_DB"],
        "user": os.environ["PG_USER"],
        "password": os.environ["PG_PASSWORD"],
        "port": os.environ.get("PG_PORT", "5432"),
        "sslmode": os.environ.get("PG_SSLMODE", "require"),
    }


def _call_insert_procedure(cursor, records: List[Dict[str, Any]]):
    procedure_name = os.getenv("PG_INSERT_PROC", "logicapp.insert_messages_batch")
    payload = json.dumps(records)
    cursor.callproc(procedure_name, [payload])


@app.function_name(name="stored-proc-rollback")
@app.route(route="stored-proc-rollback", methods=["POST"])
def stored_proc_rollback(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON payload."}),
            status_code=400,
            mimetype="application/json",
        )

    records = body.get("records", [])
    if not isinstance(records, list) or not records:
        return func.HttpResponse(
            json.dumps(
                {
                    "error": "Request body must include a non-empty array of records."
                }
            ),
            status_code=400,
            mimetype="application/json",
        )

    force_failure = bool(body.get("simulateFailure", False))

    conn = None
    try:
        conn = psycopg2.connect(**_connection_params())
        conn.autocommit = False

        with conn.cursor() as cursor:
            _call_insert_procedure(cursor, records)

            if force_failure:
                raise RuntimeError(
                    "simulateFailure=true triggered an exception after the stored procedure call."
                )

        conn.commit()

        return func.HttpResponse(
            json.dumps(
                {
                    "status": "committed",
                    "inserted": len(records),
                    "procedure": os.getenv(
                        "PG_INSERT_PROC", "logicapp.insert_messages_batch"
                    ),
                }
            ),
            status_code=200,
            mimetype="application/json",
        )

    except PsycopgError as db_err:
        logging.error("Database error occurred: %s", db_err)
        if conn:
            conn.rollback()
        return func.HttpResponse(
            json.dumps({"status": "rolled_back", "error": str(db_err)}),
            status_code=500,
            mimetype="application/json",
        )

    except Exception as exc:
        logging.error("Unexpected error: %s", exc)
        if conn:
            conn.rollback()
        return func.HttpResponse(
            json.dumps({"status": "rolled_back", "error": str(exc)}),
            status_code=500,
            mimetype="application/json",
        )

    finally:
        if conn:
            conn.close()
