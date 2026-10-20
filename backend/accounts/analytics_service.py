"""
NeuroCare Nexus — Platform Activity Pipeline (Phase C)
Analytics & Session Aggregation Service

Provides dynamic aggregation of platform usage, user presence, role statistics,
session durations, and activity trends without duplicating database records or
exposing clinical data.
"""

from datetime import timedelta
import statistics
from django.utils import timezone
from django.db.models import F, ExpressionWrapper, DurationField, Sum, Avg, Count, Min, Max, Q

from accounts.models import CustomUser, UserSession, AuditLog
from accounts.presence_service import (
    evaluate_session_presence,
    HEARTBEAT_TIMEOUT_SECONDS,
    ACTIVITY_IDLE_SECONDS
)


def get_live_sessions(current_time=None):
    """
    Retrieves all currently active or idle sessions.
    Candidate sessions must be status='ACTIVE' with a heartbeat within HEARTBEAT_TIMEOUT_SECONDS.
    """
    if current_time is None:
        current_time = timezone.now()

    threshold = current_time - timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS)
    candidates = UserSession.objects.filter(
        status='ACTIVE',
        last_heartbeat_at__gte=threshold
    ).select_related('user')

    active_sessions = []
    idle_sessions = []

    for session in candidates:
        presence = evaluate_session_presence(session, current_time=current_time)
        if presence == 'ACTIVE':
            active_sessions.append(session)
        elif presence == 'IDLE':
            idle_sessions.append(session)

    return active_sessions, idle_sessions


def get_live_user_presence(current_time=None):
    """
    Aggregates session presence at the user level, avoiding double-counting:
    - User is ACTIVE if they have at least one ACTIVE session.
    - User is IDLE if they have at least one IDLE session and NO ACTIVE session.
    """
    active_sessions, idle_sessions = get_live_sessions(current_time)

    active_user_ids = {s.user_id for s in active_sessions}
    idle_user_ids = {s.user_id for s in idle_sessions} - active_user_ids

    return active_user_ids, idle_user_ids, active_sessions, idle_sessions


def get_session_duration(session, current_time=None):
    """
    Calculates the exact elapsed duration of a UserSession in seconds.
    - For closed sessions: ended_at - started_at
    - For open sessions: current_time - started_at
    """
    if current_time is None:
        current_time = timezone.now()

    if session.status == 'CLOSED' and session.ended_at:
        dur = (session.ended_at - session.started_at).total_seconds()
    else:
        dur = (current_time - session.started_at).total_seconds()

    return max(0.0, dur)


def get_platform_overview_analytics(current_time=None):
    """
    Aggregates high-level platform activity metrics across users and sessions.
    """
    if current_time is None:
        current_time = timezone.now()

    today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)

    total_users = CustomUser.objects.count()
    active_user_ids, idle_user_ids, _, _ = get_live_user_presence(current_time)

    online_count = len(active_user_ids)
    idle_count = len(idle_user_ids)
    offline_count = max(0, total_users - (online_count + idle_count))

    # Active today: users with sessions started today or last_login today
    active_today_set = set(
        UserSession.objects.filter(started_at__gte=today_start).values_list('user_id', flat=True)
    )
    active_today_set.update(
        CustomUser.objects.filter(last_login__gte=today_start).values_list('id', flat=True)
    )
    active_today = len(active_today_set)

    new_users_today = CustomUser.objects.filter(date_joined__gte=today_start).count()
    sessions_today = UserSession.objects.filter(started_at__gte=today_start).count()
    total_sessions = UserSession.objects.count()

    # Closed sessions duration calculation via DB aggregation
    closed_stats = UserSession.objects.filter(
        status='CLOSED',
        ended_at__isnull=False
    ).annotate(
        duration=ExpressionWrapper(F('ended_at') - F('started_at'), output_field=DurationField())
    ).aggregate(
        total_dur=Sum('duration'),
        count=Count('id')
    )

    closed_dur_sec = closed_stats['total_dur'].total_seconds() if closed_stats['total_dur'] else 0.0
    closed_count = closed_stats['count'] or 0

    # Open / ongoing sessions calculation
    open_sessions = UserSession.objects.filter(
        Q(status='ACTIVE') | Q(ended_at__isnull=True)
    )
    open_dur_sec = sum(
        (current_time - s.started_at).total_seconds()
        for s in open_sessions
        if s.started_at <= current_time
    )
    open_count = open_sessions.count()

    total_usage_seconds = round(closed_dur_sec + open_dur_sec, 2)
    overall_count = closed_count + open_count
    average_duration_seconds = round(
        (total_usage_seconds / overall_count) if overall_count > 0 else 0.0, 2
    )

    return {
        "total_users": total_users,
        "online_users": online_count,
        "active_users": online_count,
        "idle_users": idle_count,
        "offline_users": offline_count,
        "active_today": active_today,
        "new_users_today": new_users_today,
        "sessions_today": sessions_today,
        "total_sessions": total_sessions,
        "total_platform_usage_seconds": total_usage_seconds,
        "average_session_duration_seconds": average_duration_seconds
    }


def get_role_platform_analytics(current_time=None):
    """
    Computes role-specific activity metrics for:
    Patient, Doctor, Caregiver, Family, Admin.
    Zero medical or clinical data exposed.
    """
    if current_time is None:
        current_time = timezone.now()

    today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
    roles = ['patient', 'doctor', 'caregiver', 'family', 'admin']

    active_user_ids, idle_user_ids, _, _ = get_live_user_presence(current_time)

    # Pre-fetch user role mappings
    user_roles = dict(CustomUser.objects.values_list('id', 'role'))

    # Active today per role
    today_active_sessions = UserSession.objects.filter(
        started_at__gte=today_start
    ).values_list('user_id', flat=True)
    today_logins = CustomUser.objects.filter(
        last_login__gte=today_start
    ).values_list('id', flat=True)

    today_users_set = set(today_active_sessions).union(set(today_logins))

    # All sessions grouped by user
    all_sessions = UserSession.objects.select_related('user').all()

    role_data = {}
    for r in roles:
        role_data[r] = {
            "role": r.capitalize(),
            "role_key": r,
            "total_users": 0,
            "active_now": 0,
            "idle_now": 0,
            "offline": 0,
            "active_today": 0,
            "sessions_today": 0,
            "total_sessions": 0,
            "total_usage_seconds": 0.0,
            "average_session_duration": 0.0
        }

    # Populate user counts
    for uid, r in user_roles.items():
        if r in role_data:
            role_data[r]["total_users"] += 1
            if uid in active_user_ids:
                role_data[r]["active_now"] += 1
            elif uid in idle_user_ids:
                role_data[r]["idle_now"] += 1

            if uid in today_users_set:
                role_data[r]["active_today"] += 1

    # Populate session counts and durations
    for s in all_sessions:
        r = s.user.role if s.user else None
        if r and r in role_data:
            role_data[r]["total_sessions"] += 1
            if s.started_at >= today_start:
                role_data[r]["sessions_today"] += 1

            dur = get_session_duration(s, current_time)
            role_data[r]["total_usage_seconds"] += dur

    # Compute averages and offline counts
    for r in roles:
        tot_users = role_data[r]["total_users"]
        act_now = role_data[r]["active_now"]
        idle_now = role_data[r]["idle_now"]
        role_data[r]["offline"] = max(0, tot_users - (act_now + idle_now))

        tot_sess = role_data[r]["total_sessions"]
        tot_dur = role_data[r]["total_usage_seconds"]
        role_data[r]["total_usage_seconds"] = round(tot_dur, 2)
        role_data[r]["average_session_duration"] = round(
            (tot_dur / tot_sess) if tot_sess > 0 else 0.0, 2
        )

    return list(role_data.values())


def get_session_aggregate_analytics(range_str='7d', current_time=None):
    """
    Computes session distribution and duration metrics for 'today', '7d', or '30d'.
    """
    if current_time is None:
        current_time = timezone.now()

    range_clean = str(range_str).strip().lower()
    if range_clean in ['today', '1d']:
        start_time = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        label = 'today'
    elif range_clean in ['30d', '30days', 'month']:
        start_time = current_time - timedelta(days=30)
        label = '30d'
    else:
        start_time = current_time - timedelta(days=7)
        label = '7d'

    sessions_qs = UserSession.objects.filter(
        started_at__gte=start_time,
        started_at__lte=current_time
    )

    total_count = sessions_qs.count()
    completed_sessions = sessions_qs.filter(status='CLOSED', ended_at__isnull=False)
    completed_count = completed_sessions.count()
    active_count = sessions_qs.filter(status='ACTIVE').count()

    durations = [get_session_duration(s, current_time) for s in sessions_qs]
    completed_durations = [
        (s.ended_at - s.started_at).total_seconds()
        for s in completed_sessions
        if s.ended_at and s.ended_at >= s.started_at
    ]

    total_usage = round(sum(durations), 2)
    avg_duration = round(sum(durations) / len(durations) if durations else 0.0, 2)
    median_duration = round(statistics.median(durations) if durations else 0.0, 2)
    shortest_duration = round(min(completed_durations) if completed_durations else 0.0, 2)
    longest_duration = round(max(durations) if durations else 0.0, 2)

    return {
        "range": label,
        "start_time": start_time.isoformat(),
        "end_time": current_time.isoformat(),
        "session_count": total_count,
        "completed_sessions": completed_count,
        "active_sessions": active_count,
        "total_usage_seconds": total_usage,
        "average_duration_seconds": avg_duration,
        "median_duration_seconds": median_duration,
        "shortest_duration_seconds": shortest_duration,
        "longest_duration_seconds": longest_duration
    }


def get_activity_trends_analytics(range_str='7d', current_time=None):
    """
    Computes real date-bucketed login and session activity trends.
    Uses actual UserSession and AuditLog database records.
    """
    if current_time is None:
        current_time = timezone.now()

    range_clean = str(range_str).strip().lower()
    if range_clean in ['30d', '30days', 'month']:
        days_count = 30
    elif range_clean in ['today', '1d']:
        days_count = 1
    else:
        days_count = 7

    today_date = current_time.date()
    # Generate list of dates from (days_count - 1) days ago up to today
    dates = [today_date - timedelta(days=i) for i in reversed(range(days_count))]

    start_date = dates[0]
    start_dt = timezone.make_aware(
        timezone.datetime.combine(start_date, timezone.datetime.min.time())
    )

    # 1. Fetch sessions in the window
    sessions = UserSession.objects.filter(
        started_at__gte=start_dt,
        started_at__lte=current_time
    ).select_related('user')

    # 2. Fetch logins from AuditLog
    login_actions = ['Login Session Initiated', 'Restricted Verification Session Initiated']
    logins = AuditLog.objects.filter(
        action__in=login_actions,
        timestamp__gte=start_dt,
        timestamp__lte=current_time
    )

    # Map logins by date
    logins_by_date = {}
    for lg in logins:
        d = lg.timestamp.date()
        logins_by_date[d] = logins_by_date.get(d, 0) + 1

    # Map sessions by date
    sessions_started_by_date = {}
    sessions_closed_by_date = {}
    active_users_by_date = {}
    duration_by_date = {}

    for s in sessions:
        d_start = s.started_at.date()
        sessions_started_by_date[d_start] = sessions_started_by_date.get(d_start, 0) + 1
        
        if d_start not in active_users_by_date:
            active_users_by_date[d_start] = set()
        active_users_by_date[d_start].add(s.user_id)

        dur = get_session_duration(s, current_time)
        duration_by_date[d_start] = duration_by_date.get(d_start, 0.0) + dur

        if s.status == 'CLOSED' and s.ended_at:
            d_end = s.ended_at.date()
            sessions_closed_by_date[d_end] = sessions_closed_by_date.get(d_end, 0) + 1

    trend_buckets = []
    for d in dates:
        d_str = d.isoformat()
        trend_buckets.append({
            "date": d_str,
            "logins": logins_by_date.get(d, 0),
            "sessions_started": sessions_started_by_date.get(d, 0),
            "sessions_closed": sessions_closed_by_date.get(d, 0),
            "active_users": len(active_users_by_date.get(d, set())),
            "total_usage_seconds": round(duration_by_date.get(d, 0.0), 2)
        })

    return {
        "range": f"{days_count}d",
        "data": trend_buckets
    }


def get_live_online_users_list(current_time=None):
    """
    Returns the list of currently relevant active/idle sessions.
    Strictly contains platform session metadata; zero clinical data.
    """
    if current_time is None:
        current_time = timezone.now()

    active_sessions, idle_sessions = get_live_sessions(current_time)
    results = []

    for s in active_sessions:
        dur = int(get_session_duration(s, current_time))
        results.append({
            "sessionId": str(s.session_id),
            "userId": s.user.id,
            "displayName": s.user.full_name or s.user.email,
            "email": s.user.email,
            "role": s.user.role,
            "presence": "ACTIVE",
            "sessionStartedAt": s.started_at.isoformat(),
            "durationSeconds": dur,
            "lastHeartbeatAt": s.last_heartbeat_at.isoformat() if s.last_heartbeat_at else None,
            "lastActivityAt": s.last_activity_at.isoformat() if s.last_activity_at else None,
            "ipAddress": s.ip_address or ""
        })

    for s in idle_sessions:
        dur = int(get_session_duration(s, current_time))
        results.append({
            "sessionId": str(s.session_id),
            "userId": s.user.id,
            "displayName": s.user.full_name or s.user.email,
            "email": s.user.email,
            "role": s.user.role,
            "presence": "IDLE",
            "sessionStartedAt": s.started_at.isoformat(),
            "durationSeconds": dur,
            "lastHeartbeatAt": s.last_heartbeat_at.isoformat() if s.last_heartbeat_at else None,
            "lastActivityAt": s.last_activity_at.isoformat() if s.last_activity_at else None,
            "ipAddress": s.ip_address or ""
        })

    # Sort: ACTIVE first, then descending by duration
    results.sort(key=lambda x: (0 if x["presence"] == "ACTIVE" else 1, -x["durationSeconds"]))
    return results


def get_individual_user_platform_analytics(user_id, current_time=None):
    """
    Returns platform usage analytics for a specific user ID.
    Strictly platform usage statistics; zero clinical data.
    """
    if current_time is None:
        current_time = timezone.now()

    user = CustomUser.objects.filter(id=user_id).first()
    if not user:
        return None

    today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
    seven_days_ago = current_time - timedelta(days=7)
    thirty_days_ago = current_time - timedelta(days=30)

    # Determine current presence for this user
    user_sessions = UserSession.objects.filter(user=user)
    threshold = current_time - timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS)
    recent_sessions = user_sessions.filter(status='ACTIVE', last_heartbeat_at__gte=threshold)

    current_presence = 'OFFLINE'
    active_session_info = None

    for s in recent_sessions:
        p = evaluate_session_presence(s, current_time=current_time)
        if p == 'ACTIVE':
            current_presence = 'ACTIVE'
            active_session_info = {
                "sessionId": str(s.session_id),
                "startedAt": s.started_at.isoformat(),
                "durationSeconds": int(get_session_duration(s, current_time)),
                "lastHeartbeatAt": s.last_heartbeat_at.isoformat() if s.last_heartbeat_at else None,
                "lastActivityAt": s.last_activity_at.isoformat() if s.last_activity_at else None
            }
            break
        elif p == 'IDLE' and current_presence != 'ACTIVE':
            current_presence = 'IDLE'
            active_session_info = {
                "sessionId": str(s.session_id),
                "startedAt": s.started_at.isoformat(),
                "durationSeconds": int(get_session_duration(s, current_time)),
                "lastHeartbeatAt": s.last_heartbeat_at.isoformat() if s.last_heartbeat_at else None,
                "lastActivityAt": s.last_activity_at.isoformat() if s.last_activity_at else None
            }

    total_sessions = user_sessions.count()
    sessions_today = user_sessions.filter(started_at__gte=today_start).count()
    sessions_7d = user_sessions.filter(started_at__gte=seven_days_ago).count()
    sessions_30d = user_sessions.filter(started_at__gte=thirty_days_ago).count()

    all_durations = [get_session_duration(s, current_time) for s in user_sessions]
    completed_durations = [
        (s.ended_at - s.started_at).total_seconds()
        for s in user_sessions.filter(status='CLOSED', ended_at__isnull=False)
        if s.ended_at and s.ended_at >= s.started_at
    ]

    total_usage = round(sum(all_durations), 2)
    avg_duration = round(sum(all_durations) / len(all_durations) if all_durations else 0.0, 2)
    longest_duration = round(max(all_durations) if all_durations else 0.0, 2)
    shortest_completed = round(min(completed_durations) if completed_durations else 0.0, 2)

    return {
        "userId": user.id,
        "displayName": user.full_name or user.email,
        "email": user.email,
        "role": user.role,
        "status": user.status,
        "approved": user.approved,
        "createdAt": user.date_joined.isoformat(),
        "lastLogin": user.last_login.isoformat() if user.last_login else None,
        "currentPresence": current_presence,
        "totalSessions": total_sessions,
        "sessionsToday": sessions_today,
        "sessionsLast7Days": sessions_7d,
        "sessionsLast30Days": sessions_30d,
        "totalUsageSeconds": total_usage,
        "averageSessionDurationSeconds": avg_duration,
        "longestSessionDurationSeconds": longest_duration,
        "shortestCompletedSessionDurationSeconds": shortest_completed,
        "activeSession": active_session_info
    }
