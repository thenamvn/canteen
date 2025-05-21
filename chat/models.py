from django.db import models
from users.models import User
from products.models import Product # Giả sử bạn muốn liên kết chat với sản phẩm

class ChatRoom(models.Model):
    # Sử dụng product_id và customer_id để tạo room name duy nhất
    # Hoặc bạn có thể tạo một UUID field cho room name
    name = models.CharField(max_length=255, unique=True) # Ví dụ: product_1_customer_5_seller_2
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='chat_rooms')
    customer = models.ForeignKey(User, related_name='customer_chat_rooms', on_delete=models.CASCADE)
    seller = models.ForeignKey(User, related_name='seller_chat_rooms', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ChatMessage(models.Model):
    room = models.ForeignKey(ChatRoom, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}"

    class Meta:
        ordering = ['timestamp']