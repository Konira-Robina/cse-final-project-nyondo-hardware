from .models import Notification


def notifications_processor(request):
    if request.user.is_authenticated:
        unread_count = Notification.unread_count(request.user)
        recent = Notification.for_user(request.user).filter(
            is_read=False
        )[:5]
        return {
            'notif_unread_count': unread_count,
            'notif_recent': recent,
        }
    return {
        'notif_unread_count': 0,
        'notif_recent': [],
    }