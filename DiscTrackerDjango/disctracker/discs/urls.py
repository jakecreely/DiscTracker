from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    # ex: /discs/1
    path("<int:item_id>/", views.detail, name="detail"),
    # ex: /discs/price-history/1 
    path("price-history/<int:item_id>/", views.price_history, name="price-history"),
]