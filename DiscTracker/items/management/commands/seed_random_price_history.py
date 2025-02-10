import random
from django.core.management.base import BaseCommand, CommandError
from items.models.db_models import Item, PriceHistory
from items.services import cex
from datetime import datetime, date, timedelta

class Command(BaseCommand):
    help = 'Seeds random price history entries for the items in the databasde'

    MAX_COUNT = 100
    MAX_PRICE = 10000
    MIN_PRICE = 0

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=10,
            help="Number of price history entries to generate per item (default: 10)",
        )
        
        parser.add_argument(
            "--start-date",
            type=str,
            default="2000-01-01"
        )
        
        parser.add_argument(
            "--end-date",
            type=str,
            default=str(date.today().strftime("%Y-%m-%d"))
        )
        
        parser.add_argument(
            "--min-price",
            type=float,
            default=0.01
        )

        parser.add_argument(
            "--max-price",
            type=float,
            default=100
        )

    def handle(self, *args, **options):
        count = options["count"]
        start_date_str = options["start_date"]
        end_date_str = options["end_date"]
        min_price = options["min_price"]
        max_price = options["max_price"]
        
        if count > self.MAX_COUNT:
            raise CommandError(f"Error: --count cannot be greater than {self.MAX_COUNT}")

        if min_price < self.MIN_PRICE:
            raise CommandError(f"Error: --min-price cannot be less than {self.MIN_PRICE}")
        
        if max_price > self.MAX_PRICE:
            raise CommandError(f"Error: --max-price cannot be greater than {self.MIN_PRICE}")

        if min_price > max_price:
            raise CommandError("Error: --min-price cannot be greater than --max_price")

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except Exception:
            raise CommandError(f"Error: Dates must be in format YYYY-MM-DD (e.g., 2024-02-10)")

        if start_date > end_date:
            raise CommandError("Error: --start-date cannot be after --end-date")
        
        self.seed_random_price_history_entries(count, start_date, end_date, min_price, max_price)
        print(f'Successfully seeded random price history entries')

    def seed_random_price_history_entries(self, count, start_date, end_date, min_price, max_price):
        items = Item.objects.all()
        
        for item in items:
            for _ in range(count):
                PriceHistory.objects.get_or_create(
                    item=item,
                    sell_price=random.uniform(min_price, max_price),
                    exchange_price=random.uniform(min_price, max_price),
                    cash_price=random.uniform(min_price, max_price),
                    date_checked=self.random_date(start_date, end_date)
                )
                
    def random_date(self, start_date, end_date):
        delta = (end_date - start_date).days
        random_days = random.randint(0, delta)
        
        return (start_date + timedelta(days=random_days))