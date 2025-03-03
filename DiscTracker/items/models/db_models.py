from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.conf import settings


class Item(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="items"
    )
    cex_id = models.CharField(
        max_length=255,
        unique=True,
        validators=[
            RegexValidator(r"^[A-Za-z0-9]+$", "ID must be alphanumeric characters")
        ],
    )
    title = models.CharField(max_length=255)
    sell_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0, "Sell Price must be greater or equal to 0"),
            MaxValueValidator(3000, "Sell Price must be less than or equal to 3000"),
        ],
    )
    exchange_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0, "Exchange Price must be greater or equal to 0"),
            MaxValueValidator(
                3000, "Exchange Price must be less than or equal to 3000"
            ),
        ],
    )
    cash_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0, "Cash Price must be greater or equal to 0"),
            MaxValueValidator(3000, "Cash Price must be less than or equal to 3000"),
        ],
    )
    last_checked = models.DateField(default=timezone.now)

    def __str__(self):
        return self.title


class PriceHistory(models.Model):
    item = models.ForeignKey(
        Item, related_name="price_history", on_delete=models.CASCADE
    )
    sell_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0, "Sell Price must be greater or equal to 0"),
            MaxValueValidator(3000, "Sell Price must be less than or equal to 3000"),
        ],
    )
    exchange_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0, "Exchange Price must be greater or equal to 0"),
            MaxValueValidator(
                3000, "Exchange Price must be less than or equal to 3000"
            ),
        ],
    )
    cash_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0, "Cash Price must be greater or equal to 0"),
            MaxValueValidator(3000, "Cash Price must be less than or equal to 3000"),
        ],
    )
    date_checked = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Price History for {self.item.title} on {self.date_checked}"
