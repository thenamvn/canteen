# chat/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import ChatRoom, User
from django.http import HttpResponseForbidden

def is_seller(user):
    return user.is_authenticated and user.is_seller

@login_required
@user_passes_test(is_seller)
def seller_chat_list_view(request):
    chat_rooms = ChatRoom.objects.filter(seller=request.user).order_by('-created_at')
    return render(request, 'chat/seller_chat_list.html', {'chat_rooms': chat_rooms})


@login_required
@user_passes_test(is_seller)
def seller_chat_room_view(request, room_id):
    chat_room = get_object_or_404(ChatRoom, id=room_id)

    # Đảm bảo seller này là người sở hữu phòng chat
    if chat_room.seller != request.user:
        return redirect('chat:seller_chat_list')

    # Lấy thông tin cần thiết để JavaScript có thể kết nối WebSocket
    # Thông tin này phải khớp với cách ChatConsumer tạo room_name
    product_id = chat_room.product.id
    # ID của người đối diện (customer)
    other_user_id = chat_room.customer.id 
    seller_id_for_ws = chat_room.seller.id


    context = {
        'chat_room': chat_room,
        'product_id_for_ws': product_id,
        'seller_id_for_ws': seller_id_for_ws, # Seller của phòng chat
        'customer_id_for_ws': other_user_id, # Customer của phòng chat
        'current_user_id_for_ws': request.user.id, # User hiện tại (chính là seller)
        'current_username_for_ws': request.user.username,
    }
    return render(request, 'chat/seller_chat_room.html', context)