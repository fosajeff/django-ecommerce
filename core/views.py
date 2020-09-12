from django.shortcuts import render
from .models import Order, OrderItem, Item


def index(request):
    context = {
        'items': Item.objects.all()
    }
    return render(request, 'items.html', context)
