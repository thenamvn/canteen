from django.db import models
from users.models import User, Address
from products.models import Product
from django.urls import reverse

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    
    PAYMENT_CHOICES = (
        ('cod', 'Cash on Delivery'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    address = models.ForeignKey(Address, on_delete=models.CASCADE, related_name='orders')
    total_amount = models.DecimalField(max_digits=12, decimal_places=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cod')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"
    
    def get_absolute_url(self):
        return reverse('orders:order_detail', kwargs={'pk': self.pk})

    def get_status_display(self):
        for code, label in self.STATUS_CHOICES:
            if code == self.status:
                return label
        return self.status
    def get_payment_method_display(self):
        for code, label in self.PAYMENT_CHOICES:
            if code == self.payment_method:
                return label
        return self.payment_method

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    product_price = models.DecimalField(max_digits=10, decimal_places=0)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Order #{self.order.id}"
    
    def get_total_price(self):
        return self.product_price * self.quantity