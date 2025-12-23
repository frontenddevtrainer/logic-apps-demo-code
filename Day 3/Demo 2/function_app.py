import json
import logging
import os
import psycopg2
import azure.functions as func

app = func.FunctionApp()

@app.function_name(name="transaction-demo")
@app.route(route="transaction-demo", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def transaction_demo(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        records = body.get("records", [])

        if not records:
            return func.HttpResponse(
                json.dumps({"error": "No records provided"}),
                status_code=400,
                mimetype="application/json"
            )

        conn = psycopg2.connect(
            host=os.environ["PG_HOST"],
            database=os.environ["PG_DB"],
            user=os.environ["PG_USER"],
            password=os.environ["PG_PASSWORD"],
            port=os.environ["PG_PORT"],
            sslmode="require"
        )

        conn.autocommit = False
        cursor = conn.cursor()

        for record in records:
            if "email" not in record:
                raise Exception("Validation failed: email missing")

            cursor.execute(
                """
                INSERT INTO logicapp.messages (email, message)
                VALUES (%s, %s)
                """,
                (record["email"], record.get("message"))
            )

        conn.commit()

        return func.HttpResponse(
            json.dumps({
                "status": "committed",
                "count": len(records)
            }),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Transaction failed: {str(e)}")

        if "conn" in locals():
            conn.rollback()

        return func.HttpResponse(
            json.dumps({
                "status": "rolled_back",
                "error": str(e)
            }),
            status_code=500,
            mimetype="application/json"
        )

    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()