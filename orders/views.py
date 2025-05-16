from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from .models import Order, OrderItem
from users.models import Address
from users.forms import AddressForm
from cart.cart import Cart
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from products.models import Product
from django.db import transaction

@login_required
def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect('cart:cart_detail')
        
    addresses = Address.objects.filter(user=request.user)
    
    if request.method == 'POST':
        # Khởi tạo form với dữ liệu POST ở đây, bất kể form_type là gì
        form = AddressForm(request.POST)
        
        form_type = request.POST.get('form_type')
        address_id = request.POST.get('address')
        
        if form_type == 'use_address' and address_id:
            address = get_object_or_404(Address, id=address_id, user=request.user)
            
            with transaction.atomic():  # Sử dụng transaction để đảm bảo tính toàn vẹn dữ liệu
                # Tạo đơn hàng mới
                order = Order.objects.create(
                    user=request.user,
                    address=address,
                    total_amount=cart.get_total_price(),
                    status='pending',
                    payment_method='cod'
                )
                
                # Tạo các mục đơn hàng và cập nhật stock
                for item in cart:
                    product = item['product']
                    quantity = item['quantity']
                    
                    # Kiểm tra xem còn đủ hàng không
                    if product.stock < quantity:
                        messages.error(request, f"Sản phẩm '{product.name}' chỉ còn {product.stock} sản phẩm.")
                        order.delete()  # Xóa đơn hàng đã tạo
                        return redirect('cart:cart_detail')
                    
                    # Giảm số lượng hàng
                    product.stock -= quantity
                    product.save()
                    
                    # Ghi log để debug (có thể xóa sau)
                    print(f"CHECKOUT - Sản phẩm {product.name}: stock giảm từ {product.stock + quantity} xuống {product.stock}")
                    
                    # Tạo OrderItem
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        product_price=item['price']
                    )
                
                # Xóa giỏ hàng sau khi tạo đơn hàng
                cart.clear()
                
                # Chuyển hướng đến trang thông báo thành công
                return redirect('orders:order_success', pk=order.id)
                
        elif form_type == 'create_address' and form.is_valid():
            # Xử lý khi người dùng tạo địa chỉ mới
            new_address = form.save(commit=False)
            new_address.user = request.user
            new_address.save()
            
            # Tiếp tục tạo đơn hàng với địa chỉ mới
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    address=new_address,
                    total_amount=cart.get_total_price(),
                    status='pending',
                    payment_method='cod'
                )
                
                # Tạo các mục đơn hàng và cập nhật stock
                for item in cart:
                    product = item['product']
                    quantity = item['quantity']
                    
                    # Kiểm tra xem còn đủ hàng không
                    if product.stock < quantity:
                        messages.error(request, f"Sản phẩm '{product.name}' chỉ còn {product.stock} sản phẩm.")
                        order.delete()
                        return redirect('cart:cart_detail')
                    
                    # Giảm số lượng hàng
                    product.stock -= quantity
                    product.save()
                    
                    # Tạo OrderItem
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        product_price=item['price']
                    )
                
                # Xóa giỏ hàng sau khi tạo đơn hàng
                cart.clear()
                
                # Chuyển hướng đến trang thông báo thành công
                return redirect('orders:order_success', pk=order.id)
        elif form_type == 'create_address':
            # Form không hợp lệ, hiển thị lỗi
            messages.error(request, "Vui lòng kiểm tra lại thông tin địa chỉ.")
        else:
            # Form type không hợp lệ hoặc không có địa chỉ được chọn
            messages.error(request, "Vui lòng chọn địa chỉ hoặc tạo địa chỉ mới.")
    else:
        form = AddressForm()
    
    return render(request, 'orders/checkout.html', {
        'addresses': addresses,
        'form': form,
        'cart': cart
    })


@login_required
def cancel_order(request, order_id):
    """Cho phép người dùng hủy đơn hàng và cập nhật lại stock"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Chỉ cho phép hủy đơn hàng nếu đơn hàng chưa giao hoặc chưa hủy
    if order.status in ['shipped', 'delivered', 'cancelled']:
        messages.error(request, "Không thể hủy đơn hàng này do đã được giao hoặc đã hủy.")
        return redirect('orders:order_detail', pk=order_id)
    
    with transaction.atomic():
        # Trả lại số lượng cho các sản phẩm trong đơn hàng
        for item in order.items.all():
            product = item.product
            product.stock += item.quantity
            product.save()
            
            # Ghi log để debug (có thể xóa sau)
            print(f"HỦY ĐƠN - Sản phẩm {product.name}: stock tăng từ {product.stock - item.quantity} lên {product.stock}")
        
        # Cập nhật trạng thái đơn hàng
        order.status = 'cancelled'
        order.save()
    
    messages.success(request, "Đơn hàng đã được hủy thành công.")
    return redirect('orders:order_list')

@login_required
def order_success(request, pk):
    order = get_object_or_404(Order, id=pk, user=request.user)
    return render(request, 'orders/success.html', {'order': order})


@login_required
@user_passes_test(lambda u: u.is_seller)
def seller_orders(request):
    """Hiển thị các đơn hàng cho seller"""
    # Lấy tất cả sản phẩm của seller này
    seller_products = Product.objects.filter(seller=request.user)
    
    # Lấy các đơn hàng có chứa sản phẩm của seller
    orders = Order.objects.filter(
        items__product__in=seller_products
    ).distinct().order_by('-created_at')
    
    return render(request, 'orders/seller/order_list.html', {'orders': orders})

@login_required
@user_passes_test(lambda u: u.is_seller)
def seller_order_detail(request, order_id):
    """Hiển thị chi tiết đơn hàng cho seller"""
    order = get_object_or_404(Order, id=order_id)
    
    # Lấy các sản phẩm của seller trong đơn hàng này
    seller_items = order.items.filter(product__seller=request.user)
    
    # Nếu không có sản phẩm nào của seller này trong đơn hàng, không cho phép xem
    if not seller_items.exists():
        messages.error(request, "Bạn không có quyền xem đơn hàng này.")
        return redirect('orders:seller_orders')
    
    return render(request, 'orders/seller/order_detail.html', {
        'order': order,
        'seller_items': seller_items
    })

@login_required
@user_passes_test(lambda u: u.is_seller)
def update_order_status(request, order_id):
    """Cập nhật trạng thái đơn hàng và quản lý stock tương ứng"""
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        
        # Kiểm tra xem đơn hàng có sản phẩm của seller này không
        seller_items = order.items.filter(product__seller=request.user)
        if not seller_items.exists():
            messages.error(request, "Bạn không có quyền cập nhật đơn hàng này.")
            return redirect('orders:seller_orders')
        
        old_status = order.status
        new_status = request.POST.get('status')
        
        # Chỉ cập nhật khi trạng thái mới hợp lệ
        if new_status and new_status in [s[0] for s in Order.STATUS_CHOICES]:
            with transaction.atomic():
                # Nếu chuyển từ trạng thái khác sang "cancelled", thì cần trả lại stock
                if new_status == 'cancelled' and old_status != 'cancelled':
                    for item in seller_items:
                        product = item.product
                        product.stock += item.quantity
                        product.save()
                        
                        # Ghi log để debug
                        print(f"SELLER HỦY - Sản phẩm {product.name}: stock tăng từ {product.stock - item.quantity} lên {product.stock}")
                
                # Nếu chuyển từ "cancelled" sang trạng thái khác, trừ lại stock
                # (Trường hợp này ít khi xảy ra nhưng vẫn cần xử lý để đảm bảo tính nhất quán)
                elif old_status == 'cancelled' and new_status != 'cancelled':
                    for item in seller_items:
                        product = item.product
                        if product.stock >= item.quantity:
                            product.stock -= item.quantity
                            product.save()
                            
                            # Ghi log để debug
                            print(f"SELLER RESTORE - Sản phẩm {product.name}: stock giảm từ {product.stock + item.quantity} xuống {product.stock}")
                        else:
                            # Nếu không đủ stock để khôi phục đơn hàng
                            messages.error(request, f"Không thể thay đổi trạng thái vì sản phẩm {product.name} không đủ số lượng.")
                            return redirect('orders:seller_order_detail', order_id=order_id)
                
                # Cập nhật trạng thái đơn hàng
                order.status = new_status
                order.save()
                
                messages.success(request, f"Cập nhật trạng thái đơn hàng thành công.")
        
    return redirect('orders:seller_order_detail', order_id=order_id)

class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders/list.html'
    context_object_name = 'orders'
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'
    
    def get_queryset(self):
        # Ensure users can only view their own orders
        return Order.objects.filter(user=self.request.user)