from __future__ import annotations

from typing import Any

from loguru import logger


class NotificationService:
    """
    Handles notifications for long-running tasks like optimization or WFO.
    Supports Webhooks and logging by default.
    """

    @staticmethod
    async def notify(user_id: str, message: str, data: dict[str, Any] | None = None) -> bool:
        """Send a notification to the user."""
        logger.info(f"NOTIFICATION for user {user_id}: {message}")
        if data:
            logger.debug(f"Notification Data: {data}")
        
        # Placeholder for Webhook/Telegram/Email integration
        return True

    @staticmethod
    async def notify_job_completion(job_id: int, status: str, result_summary: str) -> bool:
        """Specific helper for job completion."""
        return await NotificationService.notify(
            "system", 
            f"Job {job_id} {status}: {result_summary}"
        )
