from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_amount', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'created_at', 'payment_method']
    search_fields = ['user__username', 'address__recipient_name']
    inlines = [OrderItemInline]

admin.site.register(Order, OrderAdmin)