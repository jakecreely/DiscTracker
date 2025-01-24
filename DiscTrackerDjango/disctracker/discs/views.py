from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    return HttpResponse("Hello, world. You're at the disc index.")

def detail(request, item_id):
    return HttpResponse("You're looking at item %s." % item_id)

def price_history(request, item_id):
    response = "You're looking at the price history of item %s."
    return HttpResponse(response % item_id)