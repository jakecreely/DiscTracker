import csv
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from items.services import cex

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds Items into the database from a CSV file containing CEX IDs"

    def add_arguments(self, parser):
        parser.add_argument(
            "file", type=str, help="Path to the CSV file containing CEX IDs"
        )
        parser.add_argument("user_id", type=int, help="User ID to have the items")

    def handle(self, *args, **options):
        file_path = options["file"]
        user_id = options["user_id"]

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            print(f"No user found wiht ID {user_id}")
            return

        try:
            with open(file_path, newline="") as csvfile:
                id_reader = csv.reader(csvfile)
                for row in id_reader:
                    cex_id = row[0]
                    self.fetch_and_seed_data(cex_id, user)
                    print(f"Successfully processed CEX ID: {cex_id}")
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return

    def fetch_and_seed_data(self, cex_id, user):
        cex_data = cex.fetch_item(cex_id)

        if cex_data:
            item, should_create_price_history = cex.create_or_update_item(
                cex_data, user=user
            )
            if item:
                if should_create_price_history:
                    price_history = cex.create_price_history_entry(item)
                    if not price_history:
                        print(
                            f"Failed to create price history entry for CEX ID: {cex_id}"
                        )
                else:
                    print(
                        f"Didn't need to create new price history entry for CEX ID: {cex_id}"
                    )
            else:
                print(f"Failed to create item for CEX ID: {cex_id}")
        else:
            print(f"Failed to fetch data for CEX ID: {cex_id}")
