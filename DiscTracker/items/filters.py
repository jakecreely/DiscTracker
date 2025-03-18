import django_filters
from items.models.db_models import Item


class ItemFilter(django_filters.FilterSet):
    ordering = django_filters.OrderingFilter(
        fields=(
            ("title", "title"),
            ("sell_price", "sell_price"),
            ("exchange_price", "exchange_price"),
            ("cash_price", "cash_price"),
        ),
        label="Order by",
    )

    class Meta:
        model = Item
        fields = {
            "title": ["icontains"],
            "sell_price": ["lt", "gt"],
            "exchange_price": ["lt", "gt"],
            "cash_price": ["lt", "gt"],
        }

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        order_by = self.data.get("ordering")

        if order_by:
            if order_by.startswith("-"):
                queryset = queryset.order_by(order_by, "-id")  # Descending order
            else:
                queryset = queryset.order_by(order_by, "id")  # Ascending order
        return queryset
