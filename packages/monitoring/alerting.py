"""Alert rules and webhook dispatch."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class AlertRule:
    """Definition of an alert condition."""

    name: str
    condition_fn: Any  # Callable[[], bool]
    message_template: str
    cooldown_minutes: int = 60


class AlertManager:
    """Evaluate alert rules and dispatch notifications."""

    def __init__(self, webhook_url: str = "") -> None:
        self._webhook_url = webhook_url
        self._rules: list[AlertRule] = []
        self._last_fired: dict[str, datetime] = {}

    def add_rule(self, rule: AlertRule) -> None:
        self._rules.append(rule)

    def evaluate_all(self) -> list[str]:
        """Evaluate all rules and return list of fired alert messages."""
        now = datetime.now(timezone.utc)
        fired = []

        for rule in self._rules:
            last = self._last_fired.get(rule.name)
            if last and (now - last).total_seconds() < rule.cooldown_minutes * 60:
                continue

            try:
                if rule.condition_fn():
                    self._last_fired[rule.name] = now
                    fired.append(rule.message_template)
                    logger.warning("alert_fired", rule=rule.name, message=rule.message_template)
            except Exception as e:
                logger.error("alert_eval_error", rule=rule.name, error=str(e))

        return fired
