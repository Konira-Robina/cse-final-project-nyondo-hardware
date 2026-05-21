from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Notification

# Create your views here.

@login_required
def notification_list(request):
    notifications = Notification.for_user(request.user)
    unread_count = Notification.unread_count(request.user)

    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications,
        'unread_count': unread_count,
    })


@login_required
def mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    notification.is_read = True
    notification.save()

    # Redirect to the notification's link if it has one
    if notification.link:
        return redirect(notification.link)
    return redirect('notification_list')


@login_required
def mark_all_read(request):
    if request.method == 'POST':
        Notification.mark_all_read(request.user)
        messages.success(request, "All notifications marked as read.")
    return redirect('notification_list')


@login_required
def delete_notification(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    if request.method == 'POST':
        notification.delete()
        messages.success(request, "Notification deleted.")
    return redirect('notification_list')


@login_required
def delete_all_read(request):
    if request.method == 'POST':
        Notification.for_user(request.user).filter(is_read=True).delete()
        messages.success(request, "All read notifications cleared.")
    return redirect('notification_list')