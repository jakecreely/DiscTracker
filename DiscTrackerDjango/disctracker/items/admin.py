from django.contrib import admin

from items.models.db_models import Item, PriceHistory

# Register your models here.
admin.site.register(Item)
admin.site.register(PriceHistory)
