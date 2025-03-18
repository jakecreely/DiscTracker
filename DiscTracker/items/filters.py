import django_filters
from items.models.db_models import Item


class ItemFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(
        field_name="title", lookup_expr="icontains", label="Title (Search)"
    )
    sell_price_min = django_filters.NumberFilter(
        field_name="sell_price", lookup_expr="gt", label="Minimum Sell Price"
    )
    sell_price_max = django_filters.NumberFilter(
        field_name="sell_price", lookup_expr="lt", label="Maximum Sell Price"
    )
    exchange_price_min = django_filters.NumberFilter(
        field_name="exchange_price", lookup_expr="gt", label="Minimum Exchange Price"
    )
    exchange_price_max = django_filters.NumberFilter(
        field_name="exchange_price", lookup_expr="lt", label="Maximum Exchange Price"
    )
    cash_price_min = django_filters.NumberFilter(
        field_name="cash_price", lookup_expr="gt", label="Minimum Cash Price"
    )
    cash_price_max = django_filters.NumberFilter(
        field_name="cash_price", lookup_expr="lt", label="Maximum Cash Price"
    )

    ordering = django_filters.OrderingFilter(
        choices=(
            ("title", "Title (A-Z)"),
            ("-title", "Title (Z-A)"),
            ("sell_price", "Sell Price (Low to High)"),
            ("-sell_price", "Sell Price (High to Low)"),
            ("exchange_price", "Exchange Price (Low To High)"),
            ("-exchange_price", "Exchange Price (High To Low)"),
            ("cash_price", "Cash Price (Low To High)"),
            ("-cash_price", "Cash Price (High To Low)"),
            ("last_checked", "Last Price Change (Oldest First)"),
            ("-last_checked", "Last Price Change (Newest First)"),
        ),
        label="Order by",
    )

    class Meta:
        model = Item
        fields = []

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        order_by = self.data.get("ordering")

        if order_by:
            if order_by.startswith("-"):
                queryset = queryset.order_by(order_by, "-id")  # Descending order
            else:
                queryset = queryset.order_by(order_by, "id")  # Ascending order
        return queryset
