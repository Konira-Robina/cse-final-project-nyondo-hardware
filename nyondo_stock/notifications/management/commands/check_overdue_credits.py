from django.core.management.base import BaseCommand
from django.utils import timezone
from suppliers.models import SupplierCreditAccount
from notifications.utils import notify_overdue_credit
from notifications.models import Notification


class Command(BaseCommand):
    help = 'Check for overdue supplier credits and send notifications'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()

        overdue = SupplierCreditAccount.objects.filter(
            is_cleared=False,
            due_date__lt=today,
        )

        notified = 0
        for credit in overdue:
            # Avoid duplicate notifications for same credit
            already_notified = Notification.objects.filter(
                category='overdue_credit',
                link__contains=str(credit.pk),
                created_at__date=today,
            ).exists()

            if not already_notified:
                notify_overdue_credit(credit)
                notified += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Done. {notified} overdue credit notification(s) created.'
            )
        )