from django.urls import path

from items import views

app_name="items"
urlpatterns = [
    # ex: /items/    
    path("", views.index, name="index"),
    
    # ex: /items/1
    path("<str:item_id>/", views.detail, name="detail"),
    
    path("<str:item_id>/chart", views.item_price_chart, name="item-price-chart"),
    
    # ex: /items/price-history/
    path("price-history", views.price_history, name="price-history"),

    # ex: /items/add-item
    path("add-item", views.add_item_from_cex, name="add-item"),
    
    # ex: /items/update-item-prices
    path("update-item-prices", views.update_item_prices, name="update-item-prices")
]