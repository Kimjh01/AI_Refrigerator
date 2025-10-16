from django.contrib import admin
from .models import FoodItem

@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'purchase_date', 'expiry_date', 'storage_type', 'source', 'created_at')
