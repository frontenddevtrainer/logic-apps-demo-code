## Retry logic guide

This guide explains how retries work in `Day 3/Demo 3/function_app.py` and how the
shared retry policy is built in `Day 3/Demo 3/retry_policy.py`.

### Overview

There are two layers of retries:

- Host-level retry (Azure Functions host)
- App-level retry (PostgreSQL operation)

Both HTTP functions reuse the same logic via `_handle_pg_retry()` and `insert_records()`.

### Host-level retry (Azure Functions)

The host retry policy is created once by `RetryPolicyBuilder` and applied to any HTTP
function that uses the shared `@http_route(...)` decorator.

Configuration is controlled by environment variables:

- `HOST_MAX_RETRY_ATTEMPTS`
- `HOST_RETRY_DELAY_SECONDS`
- `HOST_MAX_RETRY_DELAY_SECONDS`

Strategy:

- Exponential backoff via `RetryStrategy.EXPONENTIAL_BACKOFF`
- If a retryable database error is raised out of `_handle_pg_retry()`, the host
  retries the entire function execution.

Reusable entry point:

- `retry_builder = RetryPolicyBuilder(app)`
- `http_route = retry_builder.http_route`
- `host_retry_enabled = retry_builder.enabled`

### App-level retry (PostgreSQL)

The database insert operation is wrapped by `execute_with_retry()`, which retries only
on transient Postgres errors listed in `RETRYABLE_ERRORS`.

Configuration is controlled by environment variables:

- `PG_ACTION_MAX_ATTEMPTS`
- `PG_ACTION_BASE_DELAY_SECONDS`
- `PG_ACTION_MAX_DELAY_SECONDS`

Behavior:

- Retries with exponential backoff per attempt
- If all attempts fail, it raises the last error

### Shared request flow

Both `pg_retry_demo` and `pg_retry_demo_bulk` call `_handle_pg_retry()`:

1. Parse and validate the JSON payload
2. Call `insert_records()` which uses app-level retry
3. If a retryable database error still fails, re-raise to trigger host-level retry

### Key idea

- App-level retry handles short transient database issues without rerunning the whole
  function.
- Host-level retry is a fallback if app-level retries are exhausted.
