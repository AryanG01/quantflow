"""Alert rules and webhook dispatch."""

from __future__ import annotations

import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


def send_telegram(bot_token: str, chat_id: str, message: str) -> bool:
    """Send a message via Telegram Bot API.

    Returns True on success, False on any error. Never raises.
    Uses the stdlib urllib to avoid a requests dependency.
    """
    if not bot_token or not chat_id:
        return False
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = urllib.parse.urlencode(
            {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
        ).encode()
        req = urllib.request.Request(url, data=payload, method="POST")  # noqa: S310
        with urllib.request.urlopen(req, timeout=5) as resp:  # noqa: S310
            return bool(resp.status == 200)
    except Exception as e:
        logger.warning("telegram_send_failed", error=str(e))
        return False


class AlertSeverity(Enum):
    """Alert severity levels with built-in cooldown periods."""

    LOW = 120  # minutes
    MEDIUM = 60  # minutes
    HIGH = 15  # minutes
    CRITICAL = 0  # no cooldown — fire every evaluation cycle

    @property
    def cooldown_minutes(self) -> int:
        return self.value


@dataclass
class AlertRule:
    """Definition of an alert condition."""

    name: str
    condition_fn: Any  # Callable[[], bool]
    message_template: str
    severity: AlertSeverity = AlertSeverity.MEDIUM


class AlertManager:
    """Evaluate alert rules and dispatch notifications.

    Supports:
    - Severity-based cooldown (LOW/MEDIUM/HIGH/CRITICAL)
    - Optional Telegram notification for HIGH and CRITICAL alerts
    """

    def __init__(
        self,
        webhook_url: str = "",
        telegram_bot_token: str = "",
        telegram_chat_id: str = "",
    ) -> None:
        self._webhook_url = webhook_url
        self._telegram_bot_token = telegram_bot_token
        self._telegram_chat_id = telegram_chat_id
        self._rules: list[AlertRule] = []
        self._last_fired: dict[str, datetime] = {}

    def add_rule(self, rule: AlertRule) -> None:
        self._rules.append(rule)

    def evaluate_all(self) -> list[str]:
        """Evaluate all rules and return list of fired alert messages."""
        now = datetime.now(UTC)
        fired = []

        for rule in self._rules:
            cooldown = rule.severity.cooldown_minutes
            last = self._last_fired.get(rule.name)
            if cooldown > 0 and last and (now - last).total_seconds() < cooldown * 60:
                continue

            try:
                if rule.condition_fn():
                    self._last_fired[rule.name] = now
                    fired.append(rule.message_template)
                    logger.warning(
                        "alert_fired",
                        rule=rule.name,
                        severity=rule.severity.name,
                        message=rule.message_template,
                    )
                    # Telegram: send for HIGH and CRITICAL severity
                    if rule.severity in (AlertSeverity.HIGH, AlertSeverity.CRITICAL):
                        tag = f"[{rule.severity.name}]"
                        text = f"<b>QuantFlow Alert {tag}</b>\n{rule.message_template}"
                        send_telegram(self._telegram_bot_token, self._telegram_chat_id, text)
            except Exception as e:
                logger.error("alert_eval_error", rule=rule.name, error=str(e))

        return fired
