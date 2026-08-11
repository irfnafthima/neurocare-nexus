def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def log_audit_trail(request, action, target, result='Success', actor=None):
    """
    Utility helper to log system security audit trails, capturing actors,
    IP addresses, and User Agent device footprints automatically.
    """
    from accounts.models import AuditLog
    
    user = actor or (request.user if (request and request.user and request.user.is_authenticated) else None)
    username = user.full_name if user else 'Anonymous/System'
    
    ip_address = None
    device_info = None
    if request:
        ip_address = get_client_ip(request)
        device_info = request.META.get('HTTP_USER_AGENT', '')[:255]
        
    AuditLog.objects.create(
        username=username,
        actor=user,
        action=action,
        target=target,
        status=result,
        ip_address=ip_address,
        device_info=device_info
    )
