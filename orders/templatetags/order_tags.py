from django import template

register = template.Library()

@register.filter
def sum_seller_items(items):
    """Tính tổng giá trị các sản phẩm của seller trong đơn hàng"""
    return sum(item.product_price * item.quantity for item in items)