import json
import logging
import os
import time
from typing import Any, Dict, Optional

import azure.functions as func
from applicationinsights import TelemetryClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


def _extract_instrumentation_key() -> Optional[str]:
    ikey = os.getenv("APPINSIGHTS_INSTRUMENTATIONKEY", "").strip()
    if ikey:
        return ikey

    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", "")
    for part in connection_string.split(";"):
        if part.lower().startswith("instrumentationkey="):
            return part.split("=", 1)[1].strip() or None

    return None


def _coerce_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _build_client(correlation_id: Optional[str]) -> Optional[TelemetryClient]:
    ikey = _extract_instrumentation_key()
    if not ikey:
        return None

    client = TelemetryClient(ikey)
    if correlation_id:
        client.context.operation.id = correlation_id
    return client


@app.function_name(name="custom-logger")
@app.route(route="custom-logger", methods=["POST"])
def custom_logger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Custom logger triggered")

    try:
        payload = req.get_json()
    except ValueError:
        logging.warning("Invalid JSON payload supplied.")
        return func.HttpResponse(
            "Request body must be valid JSON.", status_code=400
        )

    if not isinstance(payload, dict):
        logging.warning("JSON payload is not an object.")
        return func.HttpResponse(
            "JSON payload must be an object.", status_code=400
        )

    event_name = payload.get("eventName", "LogicAppEvent")
    properties = _coerce_dict(payload.get("properties"))
    metrics = _coerce_dict(payload.get("metrics"))
    correlation_id = payload.get("correlationId") or payload.get("operationId")

    exception_message = payload.get("exceptionMessage")
    exception_type = payload.get("exceptionType", "LogicAppError")
    severity_level = payload.get("severityLevel", 3)

    if correlation_id and "correlationId" not in properties:
        properties["correlationId"] = correlation_id

    client = _build_client(correlation_id)
    if not client:
        logging.warning("Application Insights is not configured.")
        return func.HttpResponse(
            json.dumps(
                {
                    "status": "skipped",
                    "reason": "Application Insights not configured",
                    "eventName": event_name,
                }
            ),
            status_code=200,
            mimetype="application/json",
        )

    client.track_event(event_name, properties=properties, measurements=metrics)

    tracked_exception = False
    if exception_message:
        properties.setdefault("exceptionType", exception_type)
        properties.setdefault("severityLevel", str(severity_level))
        try:
            raise RuntimeError(exception_message)
        except RuntimeError:
            client.track_exception(properties=properties, measurements=metrics)
            tracked_exception = True

    client.flush()
    time.sleep(0.25)

    return func.HttpResponse(
        json.dumps(
            {
                "status": "logged",
                "eventName": event_name,
                "trackedException": tracked_exception,
                "correlationId": correlation_id,
            }
        ),
        status_code=200,
        mimetype="application/json",
    )
