from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json


class Command(BaseCommand):
    help = "Setup update price history periodic tasks"

    def handle(self, *args, **options):
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=12, period=IntervalSchedule.HOURS
        )

        task_name = "Run Update Price History Task Every Minute"

        if not PeriodicTask.objects.filter(name=task_name).exists():
            PeriodicTask.objects.create(
                name=task_name,
                task="items.tasks.update_prices_task",
                interval=schedule,
                args=json.dumps([]),
                kwargs=json.dumps({}),
                enabled=True,
            )
            print("Successfully created update price history periodic task")
        else:
            print("Update price history task already exists.")
