"""Notifications — webhook on experiment completion."""

import json
import logging
import os
import urllib.request

logger = logging.getLogger(__name__)

WEBHOOK_URL = os.environ.get("SERVESMITH_WEBHOOK_URL")


def notify_experiment_complete(experiment_id: str, status: str, recommendations: list[dict]) -> None:
    """Send a webhook notification when an experiment finishes."""
    if not WEBHOOK_URL:
        return

    best = recommendations[0] if recommendations else None
    text = f"*ServeSmith Experiment Complete*\n" \
           f"ID: `{experiment_id}` | Status: *{status}*\n"

    if best:
        text += f"Best: {best.get('instance_type')} @ C{best.get('concurrency')} → " \
                f"{best.get('tokens_per_sec', 0):.0f} tok/s, ${best.get('cost_per_million_tokens', 0):.3f}/M tokens"

    try:
        data = json.dumps({"text": text}).encode()
        req = urllib.request.Request(WEBHOOK_URL, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5)
        logger.info(f"Webhook sent for {experiment_id}")
    except Exception as e:
        logger.warning(f"Webhook failed: {e}")
