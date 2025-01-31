from django.contrib import admin

from .models import Item, PriceHistory

# Register your models here.
admin.site.register(Item)
admin.site.register(PriceHistory)
