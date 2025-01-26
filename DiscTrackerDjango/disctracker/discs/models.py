from django.db import models
from datetime import datetime

class Item(models.Model):
    title = models.CharField(max_length=255)
    cex_id = models.CharField(max_length=255)
    sell_price = models.FloatField()
    exchange_price = models.FloatField()
    cash_price = models.FloatField()
    last_checked = models.DateField()

    def __str__(self):
        return self.title

class PriceHistory(models.Model):
    item = models.ForeignKey(Item, related_name='price_history_items', on_delete=models.CASCADE)
    sell_price = models.FloatField()
    exchange_price = models.FloatField()
    cash_price = models.FloatField()
    date_checked = models.DateField(default=datetime.now)

    def __str__(self):
        return f"Price History for {self.item.title} on {self.date_checked}"