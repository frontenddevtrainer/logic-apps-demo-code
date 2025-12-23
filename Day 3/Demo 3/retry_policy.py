import os
from datetime import timedelta
from typing import Optional

import azure.functions as func

try:
    RetryPolicy = func.RetryPolicy
    RetryStrategy = func.RetryStrategy
except AttributeError:
    try:
        from azure.functions.decorators.retry import RetryPolicy, RetryStrategy
    except ImportError:
        RetryPolicy = None
        RetryStrategy = None


class RetryPolicyBuilder:
    def __init__(self, app: func.FunctionApp) -> None:
        self._app = app
        self._policy = self._build_policy()

    @property
    def enabled(self) -> bool:
        return self._policy is not None

    @property
    def policy(self) -> Optional[RetryPolicy]:
        return self._policy

    def http_route(self, route: str, methods: Optional[list[str]] = None):
        if self._policy:
            return self._app.route(route=route, methods=methods, retry=self._policy)

        return self._app.route(route=route, methods=methods)

    def _build_policy(self) -> Optional[RetryPolicy]:
        if not (RetryPolicy and RetryStrategy):
            return None

        return RetryPolicy(
            max_retry_attempts=int(os.getenv("HOST_MAX_RETRY_ATTEMPTS", "3")),
            delay_interval=timedelta(
                seconds=int(os.getenv("HOST_RETRY_DELAY_SECONDS", "5"))
            ),
            maximum_delay_interval=timedelta(
                seconds=int(os.getenv("HOST_MAX_RETRY_DELAY_SECONDS", "20"))
            ),
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        )
