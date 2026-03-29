"""Notification service for feedback alerts."""

import os
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import models

# Configuration
FEEDBACK_NOTIFICATION_ENABLED = os.getenv("FEEDBACK_NOTIFICATION_ENABLED", "true").lower() == "true"
FEEDBACK_VOTE_THRESHOLD = int(os.getenv("FEEDBACK_VOTE_THRESHOLD", "10"))
FEEDBACK_NOTIFICATION_EMAIL = os.getenv("FEEDBACK_NOTIFICATION_EMAIL", "")
FEEDBACK_NOTIFICATION_WEBHOOK_URL = os.getenv("FEEDBACK_NOTIFICATION_WEBHOOK_URL", "")

logger = logging.getLogger(__name__)


async def check_threshold_notification_sent(
    db: AsyncSession,
    feedback_id: int,
) -> bool:
    """Check if threshold notification has already been sent for this feedback."""
    result = await db.execute(
        select(models.FeedbackNotification)
        .where(
            models.FeedbackNotification.feedback_id == feedback_id,
            models.FeedbackNotification.notification_type == "threshold_reached",
            models.FeedbackNotification.is_sent == 1,
        )
    )
    return result.scalar_one_or_none() is not None


async def create_notification_record(
    db: AsyncSession,
    feedback_id: int,
    notification_type: str,
    is_sent: bool = False,
) -> models.FeedbackNotification:
    """Create a notification record in the database."""
    notification = models.FeedbackNotification(
        feedback_id=feedback_id,
        notification_type=notification_type,
        is_sent=1 if is_sent else 0,
    )
    db.add(notification)
    await db.flush()
    await db.commit()
    await db.refresh(notification)
    return notification


async def send_threshold_notification(
    db: AsyncSession,
    feedback: models.Feedback,
) -> bool:
    """
    Send notification when feedback reaches vote threshold.
    
    Args:
        db: Database session
        feedback: Feedback object
        
    Returns:
        bool: True if notification was sent successfully
    """
    if not FEEDBACK_NOTIFICATION_ENABLED:
        logger.info(f"Notifications disabled. Would have notified about feedback #{feedback.id}")
        return False
    
    # Check if already notified
    already_notified = await check_threshold_notification_sent(db, feedback.id)
    if already_notified:
        logger.info(f"Feedback #{feedback.id} already notified, skipping")
        return False
    
    # Create notification message
    message = (
        f"🎯 Feedback #{feedback.id} has reached {feedback.vote_count} votes!\n"
        f"Category: {feedback.category}\n"
        f"Content: {feedback.content[:200]}..." if len(feedback.content) > 200 else f"Content: {feedback.content}"
    )
    
    # Send via webhook (Slack/Discord/etc.)
    if FEEDBACK_NOTIFICATION_WEBHOOK_URL:
        try:
            await _send_webhook_notification(FEEDBACK_NOTIFICATION_WEBHOOK_URL, message)
            logger.info(f"Webhook notification sent for feedback #{feedback.id}")
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
    
    # Send via email (if configured)
    if FEEDBACK_NOTIFICATION_EMAIL:
        try:
            await _send_email_notification(
                FEEDBACK_NOTIFICATION_EMAIL,
                f"Feedback #{feedback.id} reached {feedback.vote_count} votes",
                message,
            )
            logger.info(f"Email notification sent for feedback #{feedback.id}")
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    # Create notification record
    await create_notification_record(db, feedback.id, "threshold_reached", is_sent=True)
    
    return True


async def check_and_send_threshold_notification(
    db: AsyncSession,
    feedback: models.Feedback,
) -> bool:
    """
    Check if feedback has reached threshold and send notification if needed.
    
    Args:
        db: Database session
        feedback: Feedback object
        
    Returns:
        bool: True if notification was sent
    """
    if feedback.vote_count >= FEEDBACK_VOTE_THRESHOLD:
        return await send_threshold_notification(db, feedback)
    return False


async def _send_webhook_notification(webhook_url: str, message: str) -> None:
    """Send notification to webhook URL (Slack/Discord/etc.)."""
    import httpx
    
    # Format for Slack/Discord
    payload = {
        "text": message,
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(webhook_url, json=payload, timeout=10.0)
        response.raise_for_status()


async def _send_email_notification(to_email: str, subject: str, body: str) -> None:
    """
    Send email notification.
    
    Note: This is a placeholder. Implement with your email service provider
    (SendGrid, AWS SES, SMTP, etc.)
    """
    # TODO: Implement with actual email service
    logger.info(f"Email to {to_email}: {subject}\n{body}")
    
    # Example with SMTP (uncomment and configure when needed):
    # import smtplib
    # from email.mime.text import MIMEText
    #
    # msg = MIMEText(body)
    # msg['Subject'] = subject
    # msg['From'] = 'noreply@example.com'
    # msg['To'] = to_email
    #
    # with smtplib.SMTP('smtp.example.com', 587) as server:
    #     server.starttls()
    #     server.login('user', 'password')
    #     server.send_message(msg)
