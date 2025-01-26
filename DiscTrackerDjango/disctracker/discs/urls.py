from django.urls import path

from . import views

app_name="discs"
urlpatterns = [
    path("", views.index, name="index"),
    # ex: /discs/1
    path("<str:item_id>/", views.detail, name=" detail"),
    # ex: /discs/price-history/1 
    path("price-history/<str:item_id>/", views.price_history, name="price-history"),
    
    path("add-item", views.add_item_from_cex, name="add-item"),
]