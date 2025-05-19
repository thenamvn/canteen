from django.db import models
from users.models import User, Address
from products.models import Product
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
import time


class Order(models.Model):
    STATUS_CHOICES = (
        ("pending_payment", "Chờ thanh toán"),  # Trạng thái mới cho đơn hàng PayOS
        ("pending", "Đang chờ xử lý (COD)"),  # Đổi tên để rõ ràng hơn
        ("processing", "Đang xử lý"),
        ("shipped", "Đã giao hàng"),
        ("delivered", "Đã nhận hàng"),
        ("cancelled", "Đã hủy"),
        ("payment_failed", "Thanh toán thất bại"),
    )

    PAYMENT_CHOICES = (
        ("cod", "Thanh toán khi nhận hàng"),
        ("transfer", "Chuyển khoản ngân hàng (PayOS)"),
    )

    PAYOS_PAYMENT_STATUS_CHOICES = (
        ("PENDING", "Chờ thanh toán"),
        ("PAID", "Đã thanh toán"),  # PayOS thường dùng 'PAID'
        ("PROCESSING", "Đang xử lý (PayOS)"),
        ("SUCCESS", "Thành công"),  # Giữ lại nếu bạn dùng SUCCESS cho logic nội bộ
        ("FAILED", "Thất bại"),
        ("CANCELLED", "Đã hủy (PayOS)"),
        ("EXPIRED", "Đã hết hạn (PayOS)"),
        # Thêm các trạng thái khác mà PayOS có thể trả về
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    address = models.ForeignKey(
        Address, on_delete=models.CASCADE, related_name="orders"
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_CHOICES, default="cod"
    )

    # Trường cho PayOS
    payos_order_code = models.BigIntegerField(  # PayOS yêu cầu orderCode là Integer, BigInt cho timestamp
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="Mã đơn hàng duy nhất gửi cho PayOS",
    )
    payos_payment_link_id = models.CharField(  # ID của link thanh toán từ PayOS
        max_length=255,
        null=True,
        blank=True,
        help_text="ID của link thanh toán từ PayOS",
    )
    payos_payment_status = models.CharField(
        max_length=20,
        choices=PAYOS_PAYMENT_STATUS_CHOICES,
        default="PENDING",
        verbose_name="Trạng thái thanh toán PayOS",
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username} - {self.get_status_display()}"

    def get_absolute_url(self):
        return reverse("orders:order_detail", kwargs={"pk": self.pk})

    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    def get_payment_method_display(self):
        return dict(self.PAYMENT_CHOICES).get(self.payment_method, self.payment_method)

    def get_payos_payment_status_display(self):
        return dict(self.PAYOS_PAYMENT_STATUS_CHOICES).get(
            self.payos_payment_status, self.payos_payment_status
        )

    def can_be_cancelled_by_user(self):
        # Cho phép hủy nếu là 'pending_payment', hoặc 'pending' (COD) và trong một khoảng thời gian nhất định
        if self.status == "pending_payment":
            return True
        if self.status == "pending" and timezone.now() < self.created_at + timedelta(
            hours=1
        ):  # Ví dụ: hủy COD trong 1 giờ
            return True
        # Seller có thể có logic hủy khác
        return False


# OrderItem model giữ nguyên


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    product_price = models.DecimalField(max_digits=10, decimal_places=0)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Order #{self.order.id}"

    def get_total_price(self):
        return self.product_price * self.quantity
