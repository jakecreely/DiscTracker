import django_filters
from items.models.db_models import Item

class ItemFilter(django_filters.FilterSet):
    ordering = django_filters.OrderingFilter(
        fields=(
            ('title', 'title'),
            ('sell_price', 'sell_price'),
            ('exchange_price', 'exchange_price'),
            ('cash_price', 'cash_price'),
        ),
        label="Order by"
    )
    
    class Meta:
        model = Item
        fields = {
            'title': ['icontains'],
            'sell_price': ['lt', 'gt'],
            'exchange_price': ['lt', 'gt'],
            'cash_price': ['lt', 'gt'],
        }