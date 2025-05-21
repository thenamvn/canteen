# orders/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages
import time
import json
import random
from django.views.decorators.csrf import csrf_exempt

# Models
from .models import Order, OrderItem
from users.models import Address
from products.models import Product

# Forms
from users.forms import AddressForm

# Cart
from cart.cart import Cart

# PayOS
from payos import PayOS

try:
    from payos import PaymentData, ItemData
except ImportError:
    try:
        from payos import (
            PaymentData as PayOS_PaymentData_Type,
            ItemData as PayOS_ItemData_Type,
        )

        PaymentData = PayOS_PaymentData_Type
        ItemData = PayOS_ItemData_Type
        print("INFO: Imported PaymentData, ItemData from payos.types")
    except ImportError:
        PaymentData = None
        ItemData = None
        print(
            "ERROR: Không thể import PaymentData hoặc ItemData từ thư viện payos. Thanh toán PayOS có thể không hoạt động."
        )

# Khởi tạo PayOS client
try:
    payos_client = PayOS(
        client_id=settings.PAYOS_CLIENT_ID,
        api_key=settings.PAYOS_API_KEY,
        checksum_key=settings.PAYOS_CHECKSUM_KEY,
    )
    print("INFO: PayOS client initialized successfully.")
except Exception as e:
    print(f"LỖI CẤU HÌNH PAYOS: {e}")
    payos_client = None

@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, id=pk, user=request.user)
    
    # Create context with both order and cart information
    context = {
        'order': order,
        'items': order.items.all(),
        'payment_method': order.payment_method,
        'total_amount': order.total_amount,  # Use this value for display instead of cart
        'status': order.status,
    }
    
    # For orders with pending_payment or payment_failed statuses, 
    # we need special handling since cart might be cleared already
    if order.status in ['pending_payment', 'payment_failed']:
        # Create a dict structure that mimics cart for template to use
        cart_like = {
            'get_total_price': order.total_amount,
            'items': [{'product': item.product, 'quantity': item.quantity, 
                      'price': item.product_price, 'total_price': item.get_total_price()} 
                     for item in order.items.all()]
        }
        context['cart'] = cart_like
    else:
        # For other statuses, cart might be relevant if this is an active session
        # Though likely empty if order was completed
        cart = Cart(request)
        context['cart'] = cart
    
    return render(request, 'orders/order_detail.html', context)

@login_required
def checkout(request):
    if request.method == "POST" and request.POST.get("payment_method") == "transfer":
        if not payos_client:
            messages.error(
                request,
                "Hệ thống thanh toán trực tuyến đang tạm thời gián đoạn do lỗi cấu hình. Vui lòng thử lại sau hoặc chọn phương thức thanh toán khác.",
            )
            return redirect("cart:cart_detail")
        if not PaymentData or not ItemData:
            messages.error(
                request,
                "Lỗi cấu hình thư viện thanh toán PayOS (PaymentData/ItemData). Vui lòng liên hệ quản trị viên.",
            )
            return redirect("cart:cart_detail")

    cart = Cart(request)
    if len(cart) == 0:
        messages.info(request, "Giỏ hàng của bạn đang trống.")
        return redirect("cart:cart_detail")

    addresses = Address.objects.filter(user=request.user)
    form = AddressForm(request.POST or None)

    initial_address_mode = "use_existing" if addresses else "create_new"
    address_mode = initial_address_mode
    if request.method == "POST":
        address_mode_from_post = request.POST.get(
            "address_mode_explicit_choice", request.POST.get("address_mode")
        )
        if address_mode_from_post:
            address_mode = address_mode_from_post
        elif form.errors:
            address_mode = "create_new"

    if request.method == "POST":
        address_id = request.POST.get("address")
        payment_method = request.POST.get("payment_method")
        selected_address = None

        if address_mode == "use_existing":
            if not addresses:
                messages.error(
                    request,
                    "Bạn chưa có địa chỉ nào đã lưu. Vui lòng thêm địa chỉ mới.",
                )
                address_mode = (
                    "create_new"  # Switch to create new if no existing addresses
                )
            elif address_id:
                selected_address = get_object_or_404(
                    Address, id=address_id, user=request.user
                )
            else:
                messages.error(
                    request, "Vui lòng chọn một địa chỉ từ danh sách đã lưu."
                )
                return render(
                    request,
                    "orders/checkout.html",
                    {
                        "addresses": addresses,
                        "form": form,
                        "cart": cart,
                        "address_mode": address_mode,
                    },
                )

        if (
            address_mode == "create_new"
        ):  # This condition should be 'elif' or handled if already switched
            if form.is_valid():
                new_address = form.save(commit=False)
                new_address.user = request.user
                if new_address.is_default:
                    Address.objects.filter(user=request.user, is_default=True).update(
                        is_default=False
                    )
                new_address.save()
                selected_address = new_address
            else:
                messages.error(
                    request,
                    "Thông tin địa chỉ mới không hợp lệ. Vui lòng kiểm tra lại các trường được đánh dấu.",
                )
                return render(
                    request,
                    "orders/checkout.html",
                    {
                        "addresses": addresses,
                        "form": form,  # Pass the form with errors
                        "cart": cart,
                        "address_mode": "create_new",  # Keep address_mode to show the form
                    },
                )

        if not selected_address:
            # This can happen if 'use_existing' was chosen but no address_id, or form was invalid
            # The specific error messages above would have been shown.
            # Re-rendering the page with current context is generally correct here.
            return render(
                request,
                "orders/checkout.html",
                {
                    "addresses": addresses,
                    "form": form,
                    "cart": cart,
                    "address_mode": address_mode,  # Reflects the mode that led to this point
                },
            )

        if not payment_method:
            messages.error(request, "Vui lòng chọn phương thức thanh toán.")
            return render(
                request,
                "orders/checkout.html",
                {
                    "addresses": addresses,
                    "form": form,
                    "cart": cart,
                    "selected_address": selected_address,
                    "address_mode": address_mode,
                },
            )

        for item_in_cart in cart:
            try:
                product_instance = Product.objects.get(id=item_in_cart["product"].id)
                quantity_check = item_in_cart["quantity"]
                if product_instance.stock < quantity_check:
                    messages.error(
                        request,
                        f"Sản phẩm '{product_instance.name}' chỉ còn {product_instance.stock} sản phẩm trong kho. Vui lòng cập nhật giỏ hàng.",
                    )
                    return redirect("cart:cart_detail")
            except Product.DoesNotExist:
                messages.error(
                    request,
                    f"Sản phẩm với ID {item_in_cart['product'].id} không tồn tại.",
                )
                return redirect("cart:cart_detail")

        if payment_method == "cod":
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    address=selected_address,
                    total_amount=cart.get_total_price(),
                    status="pending",
                    payment_method=payment_method,
                )
                for item_in_cart in cart:
                    product = Product.objects.select_for_update().get(
                        id=item_in_cart["product"].id
                    )
                    quantity = item_in_cart["quantity"]
                    product.stock -= quantity
                    product.save()
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        product_price=item_in_cart["price"],
                    )
                cart.clear()
                messages.success(
                    request, "Đơn hàng (COD) của bạn đã được đặt thành công!"
                )
                return redirect("orders:order_success", pk=order.id)

        elif payment_method == "transfer":
            order = None  # Initialize order to None
            try:
                with transaction.atomic():
                    timestamp_ms_part = int(time.time() * 1000) % 100000000
                    user_id_part = request.user.id % 1000  # Ensure user.id is int
                    # Consider using a more robust unique ID generation if needed
                    payos_order_code_val = int(
                        f"{timestamp_ms_part:08d}{user_id_part:03d}"
                    )

                    order = Order.objects.create(
                        user=request.user,
                        address=selected_address,
                        total_amount=cart.get_total_price(),
                        status="pending_payment",
                        payment_method=payment_method,
                        payos_order_code=payos_order_code_val,
                    )

                    payos_items_list = []
                    for item_in_cart in cart:
                        OrderItem.objects.create(
                            order=order,
                            product=item_in_cart["product"],
                            quantity=item_in_cart["quantity"],
                            product_price=item_in_cart["price"],
                        )
                        payos_item = ItemData(
                            name=item_in_cart["product"].name,
                            quantity=item_in_cart["quantity"],
                            price=int(item_in_cart["price"]),
                        )
                        payos_items_list.append(payos_item)

                return_url = request.build_absolute_uri(
                    reverse_lazy("orders:payos_return")
                )
                cancel_url = request.build_absolute_uri(
                    reverse_lazy("orders:payos_cancel")
                )

                description_text = f"DH{order.payos_order_code}"
                # Check PayOS documentation for description length limits, especially if not using a PayOS-linked bank account.
                # The previous "CS99LLIO075 DH801732095" from PayOS response suggests they might prepend things.
                # For safety, you might want to keep your part short.
                # For "tài khoản ngân hàng không phải liên kết qua payOS", limit is 9 chars for your part.
                # If your order.payos_order_code itself (without "DH") fits 9 chars, that might be safer in that specific case.
                # However, your successful test used "DH TEST" or similar, and previous log showed PayOS accepted "DH801732095".
                # The 50 char limit is a general good practice.

                payment_data_obj = PaymentData(
                    orderCode=order.payos_order_code,
                    amount=int(cart.get_total_price()),
                    description=description_text,
                    items=payos_items_list,
                    cancelUrl=cancel_url,
                    returnUrl=return_url,
                    buyerName=selected_address.recipient_name
                    or request.user.get_full_name()
                    or request.user.username,
                    buyerEmail=request.user.email or "",
                    buyerPhone=selected_address.phone_number or "",
                    buyerAddress=f"{selected_address.street_address}, {selected_address.ward}, {selected_address.district}, {selected_address.city}",
                    # expiredAt=int(time.time()) + (30 * 60) # Optional
                )

                print(
                    f"DEBUG: Đối tượng PaymentData gửi đến SDK PayOS: {payment_data_obj.__dict__}"
                )

                payos_response_obj = payos_client.createPaymentLink(payment_data_obj)

                payos_response_data = {}
                if hasattr(payos_response_obj, "to_json") and callable(
                    getattr(payos_response_obj, "to_json")
                ):
                    payos_response_data = payos_response_obj.to_json()
                elif isinstance(payos_response_obj, dict):
                    payos_response_data = payos_response_obj
                else:
                    print(
                        f"DEBUG: Phản hồi từ PayOS có kiểu không xác định: {type(payos_response_obj)}"
                    )
                    # This case itself should ideally be an error before trying to parse
                    raise Exception("Kiểu phản hồi không mong đợi từ PayOS SDK")

                print(
                    f"DEBUG: Phản hồi (sau to_json() hoặc dict) từ PayOS: {payos_response_data}"
                )

                # ---- MODIFIED RESPONSE HANDLING ----
                checkout_url_from_response = payos_response_data.get("checkoutUrl")
                status_from_response = payos_response_data.get(
                    "status"
                )  # e.g., "PENDING"
                payment_link_id_from_response = payos_response_data.get("paymentLinkId")

                if checkout_url_from_response and status_from_response == "PENDING":
                    print(
                        f"INFO: PayOS checkoutUrl: {checkout_url_from_response}, paymentLinkId: {payment_link_id_from_response}"
                    )
                    if (
                        order
                    ):  # 'order' should have been created in the transaction block above
                        order.payos_payment_link_id = payment_link_id_from_response
                        # You might want to store other relevant info from payos_response_data to the order
                        # order.payos_response_snapshot = json.dumps(payos_response_data) # For audit
                        order.save()
                        print(f"INFO: Đã lưu paymentLinkId vào đơn hàng {order.id}")

                        # Clear cart only after successful payment link creation AND db update
                        cart.clear()  # Clear cart here
                        return HttpResponseRedirect(checkout_url_from_response)
                    else:
                        # This should ideally not happen if order creation was successful
                        print(
                            "CRITICAL ERROR: Biến 'order' không tồn tại sau khi tạo giao dịch DB."
                        )
                        messages.error(
                            request,
                            "Lỗi hệ thống nghiêm trọng khi xử lý đơn hàng. Vui lòng liên hệ hỗ trợ.",
                        )
                        return redirect("cart:cart_detail")

                elif checkout_url_from_response and status_from_response != "PENDING":
                    error_desc_detail = f"PayOS đã tạo link thanh toán nhưng trạng thái không phải PENDING. Status: '{status_from_response}'. Full Response: {payos_response_data}"
                    print(f"WARNING: {error_desc_detail}")
                    messages.error(
                        request,
                        f"Không thể hoàn tất yêu cầu thanh toán. Trạng thái từ PayOS: {status_from_response}. Vui lòng thử lại hoặc liên hệ hỗ trợ.",
                    )
                    if order and order.pk:
                        order.status = "payment_failed"
                        order.payos_payment_status = (
                            status_from_response or "LINK_STATUS_ERROR"
                        )
                        order.save()
                    # Do NOT clear cart here
                    return redirect("cart:cart_detail")
                else:
                    # If no checkoutUrl, or other general error from PayOS
                    # Try to get a more specific error message from PayOS response
                    # Common error fields might be 'message', 'desc', or 'error' (or 'code' if it appears for errors)
                    error_code_payos = payos_response_data.get("code")
                    error_desc_payos = (
                        payos_response_data.get("desc")
                        or payos_response_data.get("message")
                        or payos_response_data.get("error")
                    )

                    if error_desc_payos:
                        error_message_to_raise = f"Lỗi từ PayOS (code: {error_code_payos or 'N/A'}): {error_desc_payos}"
                    else:
                        error_message_to_raise = "Lỗi không xác định từ PayOS khi tạo link (không có checkoutUrl hoặc thông tin lỗi rõ ràng)."

                    # This will be caught by the broader except block below
                    raise Exception(error_message_to_raise)

            except Exception as e:
                error_message_display = (
                    f"Có lỗi xảy ra khi tạo thanh toán PayOS: {str(e)}"
                )
                print(f"CRITICAL ERROR: {error_message_display}")
                import traceback

                traceback.print_exc()  # Print full traceback to console for debugging

                messages.error(
                    request,
                    error_message_display + ". Vui lòng thử lại hoặc liên hệ hỗ trợ.",
                )
                if order and order.pk and order.status == "pending_payment":
                    order.status = "payment_failed"
                    order.payos_payment_status = (
                        "FAILED_EXCEPTION"  # Custom status for this case
                    )
                    order.save()
                # Do NOT clear cart here
                return redirect("cart:cart_detail")
        else:
            messages.error(request, "Phương thức thanh toán không hợp lệ.")
            # Fall through to render GET version of page

    # Handle GET request or if POST failed before payment_method check
    # Ensure form is initialized if it's a GET request or if form wasn't submitted/valid in POST
    if request.method == "GET" or (
        request.method == "POST"
        and not form.is_valid()
        and address_mode == "create_new"
    ):
        form = AddressForm()  # Re-initialize for GET or if new address form was invalid

    return render(
        request,
        "orders/checkout.html",
        {
            "addresses": addresses,
            "form": form,
            "cart": cart,
            "address_mode": address_mode,  # Pass current address_mode
            # "selected_address": selected_address, # Only if relevant for re-render
        },
    )


@login_required
def payos_return_view(request):
    order_code_str = request.GET.get("orderCode")
    if not order_code_str:
        messages.error(request, "Thiếu thông tin đơn hàng khi xử lý thanh toán.")
        return redirect("cart:cart_detail")  # Or to a generic error page or order list

    try:
        order_code = int(order_code_str)
        # Ensure user owns this order
        order = get_object_or_404(Order, payos_order_code=order_code, user=request.user)
    except (ValueError, Order.DoesNotExist):
        messages.error(request, "Đơn hàng không hợp lệ hoặc không tìm thấy.")
        return redirect("cart:cart_detail")

    # Idempotency: If already processed and paid, redirect to success
    if (
        order.status
        == "processing"  # Or "completed" or whatever your final paid status is
        and order.payment_method == "transfer"
        and order.payos_payment_status == "PAID"
    ):
        messages.success(
            request, f"Thanh toán cho đơn hàng #{order.id} đã được xác nhận trước đó."
        )
        return redirect("orders:order_success", pk=order.id)

    try:
        print(f"PayOS Return: Đang xác thực lại thanh toán cho order code {order_code}")
        if not payos_client:
            raise Exception("PayOS client không được khởi tạo.")

        # IMPORTANT: Verify the actual response structure of getPaymentLinkInformation
        # The following assumes it might also be flat, similar to createPaymentLink's actual response.
        # If it follows a "code"/"data" structure, this needs adjustment.
        payment_info_response_obj = payos_client.getPaymentLinkInformation(
            order.payos_order_code
        )  # Use payos_order_code stored in your order

        payment_info_data = {}
        if hasattr(payment_info_response_obj, "to_json") and callable(
            getattr(payment_info_response_obj, "to_json")
        ):
            payment_info_data = payment_info_response_obj.to_json()
        elif isinstance(payment_info_response_obj, dict):
            payment_info_data = payment_info_response_obj
        else:
            raise Exception("Kiểu phản hồi không mong đợi từ getPaymentLinkInformation")

        print(
            f"PayOS Return: Dữ liệu link từ API PayOS cho đơn {order_code}: {payment_info_data}"
        )

        actual_payos_status = payment_info_data.get("status")  # Directly get status

        if not actual_payos_status:  # If status is None or not present
            # This could happen if the API call itself failed to retrieve info,
            # or if the response structure for errors is different.
            error_desc_payos = payment_info_data.get("desc") or payment_info_data.get(
                "message"
            )
            if error_desc_payos:
                raise Exception(
                    f"Không thể lấy trạng thái thanh toán từ PayOS: {error_desc_payos}"
                )
            else:
                raise Exception(
                    f"Không thể lấy trạng thái thanh toán từ PayOS. Phản hồi: {payment_info_data}"
                )

        order.payos_payment_status = (
            actual_payos_status  # Update PayOS status on your order
        )

        if actual_payos_status == "PAID":
            if (
                order.status == "pending_payment"
            ):  # Ensure it's the correct initial status
                with transaction.atomic():
                    order.status = "processing"  # Update your order status
                    # Deduct stock
                    all_items_sufficient = True
                    for (
                        item_order
                    ) in order.items.all():  # Assuming related_name is 'items'
                        product = Product.objects.select_for_update().get(
                            pk=item_order.product.pk
                        )
                        if product.stock < item_order.quantity:
                            support_contact = getattr(
                                settings, "SUPPORT_EMAIL_OR_PHONE", "bộ phận hỗ trợ"
                            )
                            error_msg = f"Sản phẩm '{product.name}' không đủ số lượng tồn kho sau khi thanh toán thành công cho đơn hàng #{order.id}. Vui lòng liên hệ {support_contact} để được hỗ trợ và hoàn tiền nếu cần."
                            messages.error(request, error_msg)  # Inform user
                            # Critical: Log this issue for manual intervention
                            print(f"CRITICAL STOCK ISSUE: {error_msg}")
                            order.status = "payment_failed"  # Or a special status like 'paid_stock_issue'
                            order.payos_payment_status = (
                                "PAID_STOCK_ISSUE"  # Custom status
                            )
                            all_items_sufficient = False
                            # Do not rollback transaction here, payment is made. This needs manual resolution or refund via PayOS.
                            break
                        product.stock -= item_order.quantity
                        product.save()

                    if not all_items_sufficient:
                        order.save()
                        # Redirect to a page explaining the issue or order detail with error.
                        return redirect("orders:order_detail", pk=order.id)

                    order.save()
                # Cart was cleared in checkout upon successful link creation and redirection.
                # If you didn't clear it there, clear it here.
                # cart = Cart(request) # Re-initialize cart if needed
                # cart.clear()
                messages.success(
                    request, f"Thanh toán cho đơn hàng #{order.id} đã thành công!"
                )
                return redirect("orders:order_success", pk=order.id)
            elif (
                order.status == "processing" or order.status == "completed"
            ):  # Already processed
                messages.info(
                    request,
                    f"Thanh toán cho đơn hàng #{order.id} đã được xử lý trước đó.",
                )
                return redirect("orders:order_success", pk=order.id)
            else:  # Order is in an unexpected state (e.g., cancelled, failed) but PayOS says PAID
                messages.warning(
                    request,
                    f"Đơn hàng #{order.id} có trạng thái ({order.get_status_display()}) không mong đợi trong khi PayOS báo đã thanh toán (PAID). Vui lòng liên hệ hỗ trợ.",
                )
                order.save()  # Save the payos_payment_status
                return redirect("orders:order_detail", pk=order.id)

        elif actual_payos_status == "CANCELLED":
            if order.status == "pending_payment":
                order.status = "cancelled"
            order.save()
            messages.warning(
                request,
                f"Thanh toán cho đơn hàng #{order.id} đã bị hủy theo thông tin từ PayOS.",
            )
            return redirect("orders:order_detail", pk=order.id)

        elif actual_payos_status == "EXPIRED":
            if order.status == "pending_payment":
                order.status = "payment_failed"  # Or 'expired'
            order.save()
            messages.error(
                request,
                f"Phiên thanh toán cho đơn hàng #{order.id} đã hết hạn theo thông tin từ PayOS.",
            )
            return redirect("orders:order_detail", pk=order.id)

        else:  # FAILED, PENDING (still PENDING on return might be unusual unless user returns too early) or other statuses
            if order.status == "pending_payment":
                if actual_payos_status == "FAILED":
                    order.status = "payment_failed"
            order.save()
            messages.info(
                request,
                f"Trạng thái thanh toán từ PayOS cho đơn hàng #{order.id} là '{actual_payos_status}'. Đơn hàng chưa hoàn tất thanh toán.",
            )
            return redirect("orders:order_detail", pk=order.id)

    except Exception as e:
        error_message = f"Lỗi khi xử lý trang xác nhận thanh toán PayOS cho đơn hàng #{order_code_str}: {str(e)}"
        print(f"CRITICAL ERROR in payos_return_view: {error_message}")
        import traceback

        traceback.print_exc()
        messages.error(
            request,
            "Có lỗi hệ thống xảy ra khi xác nhận thanh toán. Vui lòng liên hệ bộ phận hỗ trợ.",
        )
        if "order" in locals() and order and order.pk:
            return redirect("orders:order_detail", pk=order.id)
        return redirect("cart:cart_detail")  # Fallback


@login_required
def payos_cancel_view(request):
    order_code_str = request.GET.get("orderCode")
    if not order_code_str:
        messages.warning(request, "Hủy thanh toán không rõ đơn hàng.")
        return redirect("cart:cart_detail")
    try:
        order_code = int(order_code_str)
        order = get_object_or_404(Order, payos_order_code=order_code, user=request.user)

        # Update order status if it was pending_payment
        if order.status == "pending_payment":
            order.status = "cancelled"  # User initiated cancel from PayOS page
            order.payos_payment_status = "CANCELLED"  # Reflect PayOS status
            order.save()
            messages.info(
                request,
                f"Bạn đã hủy phiên thanh toán cho đơn hàng #{order.id}. Đơn hàng đã được cập nhật trạng thái hủy.",
            )
        elif order.payos_payment_status == "CANCELLED" and order.status == "cancelled":
            messages.info(
                request,
                f"Phiên thanh toán cho đơn hàng #{order.id} đã được ghi nhận hủy trước đó.",
            )
        else:
            messages.info(
                request,
                f"Người dùng quay lại từ trang hủy của PayOS cho đơn hàng #{order.id}. Trạng thái đơn hàng hiện tại: {order.get_status_display()}.",
            )

        return redirect("orders:order_detail", pk=order.id)
    except (ValueError, Order.DoesNotExist):
        messages.error(request, "Đơn hàng không hợp lệ khi xử lý hủy thanh toán.")
        return redirect("cart:cart_detail")
    except Exception as e:
        messages.error(request, f"Lỗi khi xử lý hủy thanh toán: {str(e)}")
        print(f"ERROR in payos_cancel_view: {str(e)}")
        # Potentially redirect to order detail if order object exists
        return redirect("cart:cart_detail")


@csrf_exempt
def payos_webhook_view(request):
    if request.method == "POST":
        webhook_data_raw = request.body
        try:
            # IMPORTANT: Implement signature verification from PayOS
            # payos_signature = request.headers.get('X-PayOS-Signature') # Check actual header name
            # if not payos_client.verifyPaymentWebhookData(webhook_data_raw_bytes, payos_signature):
            #     print("PayOS Webhook ERROR: Invalid signature")
            #     return JsonResponse({'code': '02', 'desc': 'Invalid signature'}, status=400)
            # For now, assuming signature verification is handled or to be added.

            webhook_data = json.loads(webhook_data_raw)
            print(f"PayOS Webhook INFO: Received data: {webhook_data}")

            # PayOS webhook structure can be { "code": "00", "desc": "...", "data": { ACTUAL_TRANSACTION_DATA } }
            # Or it could be the transaction data directly if 'data' field is not present at top level
            # The verifyPaymentWebhookData method from SDK might return the "data" part directly if signature is valid.
            # Let's assume webhook_data directly contains the fields or has a 'data' field.

            transaction_data = webhook_data.get(
                "data", webhook_data
            )  # Prefer 'data' if exists

            payos_order_code_str = transaction_data.get("orderCode")
            actual_payos_status = transaction_data.get(
                "status"
            )  # e.g., PAID, CANCELLED

            if not payos_order_code_str or not actual_payos_status:
                print(
                    f"PayOS Webhook WARNING: Missing orderCode or status in webhook data: {transaction_data}"
                )
                return JsonResponse(
                    {"code": "03", "desc": "Missing or invalid data in webhook"},
                    status=200,
                )  # PayOS expects 200 OK

            payos_order_code = int(payos_order_code_str)

            with transaction.atomic():  # Process order update within a transaction
                try:
                    order = Order.objects.select_for_update().get(
                        payos_order_code=payos_order_code
                    )
                except Order.DoesNotExist:
                    print(
                        f"PayOS Webhook ERROR: Order with payos_order_code {payos_order_code} not found."
                    )
                    return JsonResponse(
                        {"code": "05", "desc": "Order not found"}, status=200
                    )  # 200 OK as per PayOS docs

                # Idempotency: Check if this status update has already been processed
                if order.payos_payment_status == actual_payos_status:
                    # Further check if application status also reflects this, e.g. PAID and order.status is processing/completed
                    if (
                        actual_payos_status == "PAID"
                        and order.status in ["processing", "completed"]
                    ) or (
                        actual_payos_status in ["CANCELLED", "EXPIRED", "FAILED"]
                        and order.status in ["cancelled", "payment_failed"]
                    ):
                        print(
                            f"PayOS Webhook INFO: Event for order {order.id} with status {actual_payos_status} already processed."
                        )
                        return JsonResponse(
                            {"code": "00", "desc": "Event already processed"},
                            status=200,
                        )

                order.payos_payment_status = actual_payos_status
                print(
                    f"PayOS Webhook INFO: Updating order {order.id} with PayOS status: {actual_payos_status}"
                )

                if actual_payos_status == "PAID":
                    if (
                        order.status == "pending_payment"
                    ):  # Process only if it was pending
                        order.status = "processing"
                        # Deduct stock
                        for item_order_wh in order.items.all():
                            product_wh = Product.objects.select_for_update().get(
                                pk=item_order_wh.product.pk
                            )
                            if product_wh.stock < item_order_wh.quantity:
                                print(
                                    f"CRITICAL STOCK ISSUE (Webhook): Product {product_wh.name} stock insufficient for order {order.id}. Payment was PAID."
                                )
                                order.status = "payment_failed"  # Or custom status 'paid_stock_issue'
                                order.payos_payment_status = "PAID_STOCK_ISSUE_WH"
                                # This situation requires manual intervention / refund.
                                break
                            product_wh.stock -= item_order_wh.quantity
                            product_wh.save()

                        if (
                            order.status == "processing"
                        ):  # If stock deduction was successful
                            print(
                                f"PayOS Webhook: Order {order.id} status updated to 'processing', stock updated."
                            )
                        # No cart clearing here as webhook is out of user session
                    elif order.status not in ["processing", "completed"]:
                        print(
                            f"PayOS Webhook WARNING: Order {order.id} received PAID webhook but order status is '{order.status}'. Updating to processing."
                        )
                        order.status = (
                            "processing"  # Or investigate why it's in this state
                        )

                elif actual_payos_status == "CANCELLED":
                    if order.status == "pending_payment":
                        order.status = "cancelled"
                        print(
                            f"PayOS Webhook: Order {order.id} status updated to 'cancelled'."
                        )

                elif (
                    actual_payos_status == "EXPIRED" or actual_payos_status == "FAILED"
                ):
                    if order.status == "pending_payment":
                        order.status = "payment_failed"
                        print(
                            f"PayOS Webhook: Order {order.id} status updated to 'payment_failed' due to PayOS status '{actual_payos_status}'."
                        )

                else:  # Other statuses
                    print(
                        f"PayOS Webhook: Order {order.id} received unhandled PayOS status '{actual_payos_status}'."
                    )

                order.save()
            return JsonResponse(
                {"code": "00", "desc": "Webhook processed successfully"}, status=200
            )

        except json.JSONDecodeError:
            print("PayOS Webhook ERROR: Invalid JSON in webhook body.")
            return JsonResponse(
                {"code": "07", "desc": "Invalid JSON"}, status=400
            )  # 400 for invalid payload
        except Exception as e:
            print(f"PayOS Webhook CRITICAL ERROR: {str(e)}")
            import traceback

            traceback.print_exc()
            # Return 200 OK to PayOS to prevent retries for unrecoverable app errors, but log it.
            return JsonResponse(
                {
                    "code": "08",
                    "desc": "Internal server error during webhook processing",
                },
                status=200,
            )

    return JsonResponse({"code": "09", "desc": "Invalid request method"}, status=405)


@login_required
def order_success(request, pk):
    order = get_object_or_404(Order, id=pk, user=request.user)
    # Ensure only the user who made the order can see the success page, or if it's a generic success page
    return render(request, "orders/success.html", {"order": order})


@login_required
def cancel_order(request, order_id):  # User initiated cancellation from within the app
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if (
        not order.can_be_cancelled_by_user()
    ):  # Implement this method in your Order model
        messages.error(
            request, "Đơn hàng này không thể hủy hoặc đã quá thời gian cho phép hủy."
        )
        return redirect("orders:order_detail", pk=order_id)

    with transaction.atomic():
        original_status = order.status
        stock_restored_for_seller_items = False

        # For COD orders or unpaid transfer orders, can directly cancel and restore stock
        if (order.payment_method == "cod" and order.status == "pending") or (
            order.payment_method == "transfer" and order.status == "pending_payment"
        ):

            for item in order.items.all():
                product = Product.objects.select_for_update().get(pk=item.product.pk)
                product.stock += item.quantity
                product.save()
            stock_restored_for_seller_items = True

            order.status = "cancelled"
            if order.payment_method == "transfer" and order.payos_payment_link_id:
                order.payos_payment_status = "CANCELLED_BY_USER"  # Custom status
                # Optionally, try to cancel the payment link via PayOS API if it's still active and unpaid
                try:
                    if (
                        payos_client and order.payos_payment_link_id
                    ):  # and current payos status is PENDING/ACTIVE
                        # Check current link status from PayOS before attempting to cancel
                        # link_info = payos_client.getPaymentLinkInformation(order.payos_order_code)
                        # if link_info.get("status") == "PENDING":
                        #     cancellation_response = payos_client.cancelPaymentLink(order.payos_order_code)
                        #     print(f"PayOS cancelPaymentLink response for order {order.id}: {cancellation_response}")
                        pass  # Add PayOS link cancellation logic here if desired
                except Exception as e_cancel_sdk:
                    print(
                        f"Lỗi khi cố gắng hủy link PayOS (người dùng hủy đơn) cho đơn {order.payos_order_code}: {e_cancel_sdk}"
                    )

            messages.success(
                request,
                f"Đơn hàng #{order.id} đã được hủy thành công."
                + (
                    " Kho hàng đã được cập nhật."
                    if stock_restored_for_seller_items
                    else ""
                ),
            )

        elif (
            order.payment_method == "transfer"
            and order.status == "processing"
            and order.payos_payment_status == "PAID"
        ):
            # This is a more complex case: order is paid and processing.
            # Cancellation here usually means initiating a refund.
            # This might require admin approval or specific refund policies.
            # For now, let's assume user cannot directly cancel a PAID and PROCESSING order without admin.
            # If they can, you need to call PayOS refund API.
            messages.error(
                request,
                "Đơn hàng đã thanh toán và đang xử lý không thể hủy trực tiếp. Vui lòng liên hệ hỗ trợ để yêu cầu hoàn tiền.",
            )
            return redirect("orders:order_detail", pk=order_id)

        else:
            # Other statuses that might not be cancellable by user directly
            messages.error(
                request,
                f"Đơn hàng ở trạng thái '{order.get_status_display()}' không thể hủy theo cách này.",
            )
            return redirect("orders:order_detail", pk=order_id)

        order.save()
    return redirect("orders:order_list")


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "orders/list.html"
    context_object_name = "orders"
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by("-created_at")


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "orders/order_detail.html"
    context_object_name = "order"

    def get_queryset(self):
        # Ensure user can only see their own orders
        return Order.objects.filter(user=self.request.user)


# --- SELLER VIEWS ---
@login_required
@user_passes_test(lambda u: hasattr(u, "is_seller") and u.is_seller)
def seller_orders(request):
    order_ids = (
        OrderItem.objects.filter(product__seller=request.user)
        .values_list("order_id", flat=True)
        .distinct()
    )
    orders = Order.objects.filter(id__in=order_ids).order_by("-created_at")
    return render(request, "orders/seller/order_list.html", {"orders": orders})


@login_required
@user_passes_test(lambda u: hasattr(u, "is_seller") and u.is_seller)
def seller_order_detail(request, order_id):
    # Seller should be able to see order details if at least one item in the order belongs to them
    order = get_object_or_404(Order, id=order_id)
    seller_items = order.items.filter(product__seller=request.user)
    if not seller_items.exists():
        messages.error(request, "Đơn hàng này không chứa sản phẩm nào của bạn.")
        return redirect("orders:seller_orders")  # Or an appropriate error page
    return render(
        request,
        "orders/seller/order_detail.html",
        {"order": order, "seller_items": seller_items},
    )


@login_required
@user_passes_test(lambda u: hasattr(u, "is_seller") and u.is_seller)
def update_order_status(request, order_id):
    if request.method == "POST":
        order = get_object_or_404(Order, id=order_id)
        if not order.items.filter(product__seller=request.user).exists():
            messages.error(
                request, "Bạn không có quyền cập nhật trạng thái cho đơn hàng này."
            )
            return redirect("orders:seller_orders")

        new_status_from_form = request.POST.get("status")

        # Lấy STATUS_CHOICES từ model Order để validate
        # Giả sử Order model đã được import: from .models import Order
        valid_statuses = [s[0] for s in Order.STATUS_CHOICES]
        if not new_status_from_form or new_status_from_form not in valid_statuses:
            messages.error(request, "Trạng thái cập nhật không hợp lệ.")
            return redirect("orders:seller_order_detail", order_id=order_id)

        old_status = order.status
        if new_status_from_form == old_status:
            messages.info(request, "Trạng thái đơn hàng không thay đổi.")
            return redirect("orders:seller_order_detail", order_id=order_id)

        with transaction.atomic():
            order.status = new_status_from_form  # Gán giá trị mới

            # Logic hoàn kho (giữ nguyên như trước)
            if new_status_from_form == "cancelled" and old_status in [
                "pending",
                "processing",
            ]:
                restored_info = []
                for item in order.items.filter(product__seller=request.user):
                    if old_status in ["pending", "processing"]:
                        prod = Product.objects.select_for_update().get(
                            pk=item.product.pk
                        )
                        prod.stock += item.quantity
                        prod.save()
                        restored_info.append(f"{prod.name} (+{item.quantity})")
                if restored_info:
                    messages.info(
                        request,
                        f"Đã hoàn lại kho cho các sản phẩm: {', '.join(restored_info)}.",
                    )

            order.save()

            # ---- SỬA THÔNG BÁO CHO ĐÚNG Ý MUỐN ----
            # Tạo text hiển thị tùy chỉnh cho thông báo
            display_text_for_message = ""
            if order.status == "shipped":
                display_text_for_message = "Đang giao hàng"  # Hiển thị đúng ý muốn
            elif order.status == "delivered":
                # Trong STATUS_CHOICES của bạn: ("delivered", "Đã nhận hàng")
                # Trong template select option: <option value="delivered"...>Đã giao hàng</option>
                # Để nhất quán, nếu bạn chọn "Đã giao hàng" (gửi value="delivered") từ form,
                # thông báo nên là "Đã giao hàng (khách đã nhận)" hoặc "Đã nhận hàng"
                display_text_for_message = "Đã nhận hàng"  # Hoặc "Đã giao hàng (khách đã nhận)" nếu text trong select là "Đã giao hàng"
            else:
                # Đối với các trạng thái khác, dùng get_status_display() như bình thường
                # Tuy nhiên, bạn cần đảm bảo các label khác trong STATUS_CHOICES cũng chính xác
                display_text_for_message = order.get_status_display()

            messages.success(
                request,
                f"Đã cập nhật trạng thái đơn hàng #{order.id} thành '{display_text_for_message}'.",
            )

        return redirect("orders:seller_order_detail", order_id=order_id)

    messages.error(request, "Yêu cầu không hợp lệ.")
    return redirect("orders:seller_orders")
