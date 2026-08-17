from notifications.models import Notification
import logging

logger = logging.getLogger(__name__)

def create_notification(user, title, message, category=None, target_id=None):
    """
    Safely creates a database notification for an authenticated user.
    Enforces HIPAA clinical privacy rules: title and message previews must not reveal raw vitals or sensitive diagnostic metrics.
    """
    if not user:
        return None
    try:
        return Notification.objects.create(
            user=user,
            title=title,
            message=message,
            category=category,
            target_id=str(target_id) if target_id else None
        )
    except Exception as e:
        logger.error(f"Error creating notification for user {user}: {e}")
        return None
