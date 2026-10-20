"""
NeuroCare Nexus — Platform Activity Pipeline (Phase B)
Presence Evaluation Service

Provides dynamic, deterministic presence calculations for UserSessions.
Evaluated dynamically from timestamps; avoids storing stale status.
"""

from datetime import timedelta
from django.utils import timezone

# Standard operational threshold constants
HEARTBEAT_TIMEOUT_SECONDS = 120   # 2 minutes: after which a session is considered OFFLINE
ACTIVITY_IDLE_SECONDS = 300       # 5 minutes: after which a session with active heartbeat is IDLE


def evaluate_session_presence(session, current_time=None) -> str:
    """
    Dynamically computes the presence status for a given UserSession.

    Rules:
    1. OFFLINE (Strict priority):
       - Session object is None or session.status == 'CLOSED'
       - session.last_heartbeat_at is None
       - Heartbeat age > 120 seconds (2 minutes)
    2. ACTIVE:
       - Heartbeat age <= 120 seconds AND activity age <= 300 seconds (5 minutes)
    3. IDLE:
       - Heartbeat age <= 120 seconds AND activity age > 300 seconds (5 minutes)

    Returns:
       'ACTIVE' | 'IDLE' | 'OFFLINE'
    """
    if not session or getattr(session, 'status', None) == 'CLOSED':
        return 'OFFLINE'

    last_heartbeat = getattr(session, 'last_heartbeat_at', None)
    if not last_heartbeat:
        return 'OFFLINE'

    if current_time is None:
        current_time = timezone.now()

    # Timezone-aware elapsed calculation
    heartbeat_elapsed = (current_time - last_heartbeat).total_seconds()

    # A stale heartbeat (> 2 min) or excessive clock distortion (> 30s in future) -> OFFLINE
    if heartbeat_elapsed > HEARTBEAT_TIMEOUT_SECONDS or heartbeat_elapsed < -30:
        return 'OFFLINE'

    # Determine relevant activity timestamp (fallback to started_at if last_activity_at not yet recorded)
    last_act = getattr(session, 'last_activity_at', None) or getattr(session, 'started_at', None)
    if not last_act:
        return 'IDLE'

    activity_elapsed = (current_time - last_act).total_seconds()
    # Normalize minor negative clock skew
    if activity_elapsed < 0:
        activity_elapsed = 0

    if activity_elapsed <= ACTIVITY_IDLE_SECONDS:
        return 'ACTIVE'
    else:
        return 'IDLE'
