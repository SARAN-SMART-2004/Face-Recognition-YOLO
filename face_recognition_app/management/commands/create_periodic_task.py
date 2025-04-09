from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json

class Command(BaseCommand):
    help = "Create periodic task for sending attendance emails"

    def handle(self, *args, **kwargs):
        schedule, _ = IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.MINUTES)
        
        task, created = PeriodicTask.objects.get_or_create(
            name="Send Attendance Email Task",
            defaults={
                'interval': schedule,
                'task': 'face_recognition_app.tasks.send_attendance_email',
                'args': json.dumps([])
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS('Periodic task created.'))
        else:
            self.stdout.write(self.style.WARNING('Periodic task already exists.'))
