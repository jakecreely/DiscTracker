import csv
from django.core.management.base import BaseCommand
from items.services import cex

class Command(BaseCommand):
    help = 'Seeds Items into the database from a CSV file containing CEX IDs'

    def add_arguments(self, parser):
        parser.add_argument('file', type=str, help="Path to the CSV file containing CEX IDs")

    def handle(self, *args, **options):
        file_path = options['file']

        try:
            with open(file_path, newline='') as csvfile:
                id_reader = csv.reader(csvfile)
                for row in id_reader:
                    cex_id = row[0]
                    self.fetch_and_seed_data(cex_id)
                    print(f'Successfully processed CEX ID: {cex_id}')
        except FileNotFoundError:
            print(f'File not found: {file_path}')

    def fetch_and_seed_data(self, cex_id):
        cex_data = cex.fetch_item(cex_id)

        if cex_data:
            item = cex.create_or_update_item(cex_data)
            if item:
                price_history = cex.create_price_history_entry(item)
                if not price_history:
                    print(f'Failed to create price history entry for CEX ID: {cex_id}')
            else:
                print(f'Failed to create item for CEX ID: {cex_id}')
        else:
            print(f'Failed to fetch data for CEX ID: {cex_id}')