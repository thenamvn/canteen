from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from .models import Order, OrderItem
from users.models import Address
from users.forms import AddressForm
from cart.cart import Cart

@login_required
def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect('cart:cart_detail')
    
    # Get user's addresses
    addresses = Address.objects.filter(user=request.user)
    
    # Handle new address form
    if request.method == 'POST':
        # Check if user selected existing address or adding new one
        address_id = request.POST.get('address_id')
        
        if address_id:
            # User selected an existing address
            address = get_object_or_404(Address, id=address_id, user=request.user)
        else:
            # User is adding a new address
            form = AddressForm(request.POST)
            if form.is_valid():
                address = form.save(commit=False)
                address.user = request.user
                address.save()
            else:
                return render(request, 'orders/checkout.html', {
                    'addresses': addresses,
                    'form': form,
                    'cart': cart
                })
        
        # Create the order
        order = Order.objects.create(
            user=request.user,
            address=address,
            total_amount=cart.get_total_price(),
            payment_method='cod'
        )
        
        # Create order items
        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                product_price=item['price']
            )
        
        # Clear the cart
        cart.clear()
        
        # Redirect to thank you page
        return redirect('orders:order_success', pk=order.id)
    
    else:
        form = AddressForm()
    
    return render(request, 'orders/checkout.html', {
        'addresses': addresses,
        'form': form,
        'cart': cart
    })

@login_required
def order_success(request, pk):
    order = get_object_or_404(Order, id=pk, user=request.user)
    return render(request, 'orders/success.html', {'order': order})

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