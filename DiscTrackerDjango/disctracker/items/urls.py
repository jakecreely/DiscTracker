from django.urls import path

from . import views

app_name="items"
urlpatterns = [
    # ex: /discs/    
    path("", views.index, name="index"),
    
    # ex: /discs/1
    path("<str:item_id>/", views.detail, name="detail"),
    
    # ex: /discs/price-history/1 
    path("price-history/<str:item_id>/", views.price_history, name="price-history"),

    # ex: /discs/add-item
    path("add-item", views.add_item_from_cex, name="add-item"),
    
    # ex: /discs/update-item-prices
    path("update-item-prices", views.update_item_prices, name="update-item-prices")
]