import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
# from .models import ChatMessage, ChatRoom, User, Product 
from django.shortcuts import get_object_or_404 # get_object_or_404 không dùng trong consumer async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Lấy thông tin từ URL và scope
        self.product_id = self.scope['url_route']['kwargs']['product_id']
        self.url_seller_id = self.scope['url_route']['kwargs']['seller_id']
        self.connecting_user = self.scope['user'] # User đang thực hiện kết nối WebSocket

        if not self.connecting_user.is_authenticated:
            print(f"ChatConsumer: User not authenticated. Closing connection.")
            await self.close()
            return

        print(f"ChatConsumer: User {self.connecting_user.username} (ID: {self.connecting_user.id}) connecting for product {self.product_id}, url_seller_id {self.url_seller_id}")

        self.chat_room_instance = await self.get_or_create_chat_room()
        
        if not self.chat_room_instance:
            print(f"ChatConsumer: Could not get/create chat room. Closing connection.")
            await self.close(code=4001) 
            return

        #room_name và room_group_name dựa trên instance đã lấy/tạo
        self.room_name = self.chat_room_instance.name 
        self.room_group_name = f'group_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        print(f"ChatConsumer: WebSocket accepted for room {self.room_name}")

        # send_chat_history dùng self.chat_room_instance
        await self.send_chat_history()
        print(f"ChatConsumer: Chat history sent for room {self.room_name}")


    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            print(f"ChatConsumer: User {self.connecting_user.username} disconnected from room {self.room_name}, code={close_code}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_content = text_data_json['message']
            sender = self.connecting_user # Sử dụng self.connecting_user đã lưu

            # save_message dùng self.chat_room_instance
            chat_message = await self.save_message(sender, message_content)
            if not chat_message: # Nếu save_message trả về None do lỗi
                print(f"ChatConsumer: Failed to save message for room {self.room_name}")
                return # Không gửi gì nếu không lưu được

            print(f"ChatConsumer: Message from {sender.username} saved to room {self.room_name}: {message_content[:30]}")

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_content,
                    'sender_id': sender.id,
                    'sender_username': sender.username,
                    'timestamp': chat_message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                }
            )
        except json.JSONDecodeError:
            print(f"ChatConsumer: Received invalid JSON: {text_data}")
        except KeyError:
            print(f"ChatConsumer: Received JSON without 'message' key: {text_data_json}")
        except Exception as e_recv:
            print(f"ChatConsumer ERROR in receive(): {type(e_recv).__name__} - {e_recv}")
            import traceback
            traceback.print_exc()


    async def chat_message(self, event):
        message = event['message']
        sender_id = event['sender_id']
        sender_username = event['sender_username']
        timestamp = event['timestamp']

        await self.send(text_data=json.dumps({
            'message': message,
            'sender_id': sender_id,
            'sender_username': sender_username,
            'timestamp': timestamp
        }))

    @database_sync_to_async
    def get_or_create_chat_room(self):
        from .models import ChatRoom
        from products.models import Product
        from users.models import User

        try:
            print(f"DB_get_or_create_chat_room: connecting_user_id={self.connecting_user.id}, product_id={self.product_id}, url_seller_id={self.url_seller_id}")

            product_obj = Product.objects.get(id=self.product_id)
            seller_of_product = product_obj.seller # Đây là User object của người bán sản phẩm

            customer_obj = None
            # Xác định ai là customer và ai là seller cho bản ghi ChatRoom
            if self.connecting_user.id != seller_of_product.id:
                # Người kết nối không phải là người bán sản phẩm => người kết nối là customer
                customer_obj = self.connecting_user
                # seller_for_db đã được xác định là seller_of_product
            else:
                query_string = self.scope.get('query_string', b'').decode() # Lấy an toàn, mặc định là byte rỗng
                params = {}
                if query_string:
                    try:
                        params = dict(qc.split("=") for qc in query_string.split("&") if qc and '=' in qc)
                    except ValueError:
                        print("DB_get_or_create_chat_room: Error parsing query string.")
                        return None
                
                other_user_id_str = params.get('other_user_id')
                
                if not other_user_id_str:
                    print(f"DB_get_or_create_chat_room: Seller {self.connecting_user.username} (product {self.product_id}) connecting without other_user_id (customer_id).")
                    return None # Seller phải chỉ định customer khi kết nối
                try:
                    customer_obj = User.objects.get(id=int(other_user_id_str))
                except User.DoesNotExist:
                    print(f"DB_get_or_create_chat_room: Customer with id {other_user_id_str} not found (for seller {self.connecting_user.username}).")
                    return None
                except ValueError: # Nếu other_user_id_str không phải là số nguyên
                    print(f"DB_get_or_create_chat_room: Invalid customer_id format: {other_user_id_str}.")
                    return None
            
            if not customer_obj: # Double check
                print("DB_get_or_create_chat_room: Customer object could not be determined.")
                return None

            # Tên phòng chuẩn để đảm bảo tính duy nhất
            standard_room_name = f"prod{product_obj.id}_cust{customer_obj.id}_sell{seller_of_product.id}"
            print(f"DB_get_or_create_chat_room: Attempting to get/create ChatRoom with name: {standard_room_name}")

            room, created = ChatRoom.objects.get_or_create(
                name=standard_room_name,
                defaults={
                    'product': product_obj,
                    'customer': customer_obj,
                    'seller': seller_of_product
                }
            )
            if created:
                print(f"DB_ChatRoom CREATED: {room.name} (ID: {room.id}) for Product: {product_obj.name}, Customer: {customer_obj.username}, Seller: {seller_of_product.username}")
            else:
                print(f"DB_ChatRoom FOUND: {room.name} (ID: {room.id})")
            return room

        except Product.DoesNotExist:
            print(f"DB_get_or_create_chat_room: Product with id {self.product_id} does not exist.")
            return None
        except User.DoesNotExist: # Xử lý trường hợp seller_of_product không tồn tại (dù product.seller nên luôn có)
            print(f"DB_get_or_create_chat_room: A User (product's seller) involved does not exist.")
            import traceback
            traceback.print_exc() # In traceback nếu có lỗi không mong muốn
            return None
        except Exception as e_room:
            print(f"DB_UNEXPECTED ERROR in get_or_create_chat_room: {type(e_room).__name__} - {e_room}")
            import traceback
            traceback.print_exc()
            return None

    @database_sync_to_async
    def save_message(self, sender_user, content):
        from .models import ChatMessage
        try:
            if not self.chat_room_instance:
                print("DB_save_message: chat_room_instance is None. Cannot save message.")
                return None

            message = ChatMessage.objects.create(
                room=self.chat_room_instance,
                sender=sender_user,
                content=content
            )
            print(f"DB_Message saved: ID {message.id} in room {self.chat_room_instance.name}")
            return message
        except Exception as e_save:
            print(f"DB_ERROR in save_message: {type(e_save).__name__} - {e_save}")
            import traceback
            traceback.print_exc()
            return None


    @database_sync_to_async
    def get_chat_history(self):
        from .models import ChatMessage
        try:
            if not self.chat_room_instance:
                print("DB_get_chat_history: chat_room_instance is None.")
                return []
            
            history = list(
                ChatMessage.objects.filter(room=self.chat_room_instance)
                .order_by('-timestamp')[:50] 
                .values('sender__id', 'sender__username', 'content', 'timestamp')
            )
            print(f"DB_get_chat_history: Found {len(history)} messages for room {self.chat_room_instance.name}")
            return history[::-1] # Reverse để gửi từ cũ nhất đến mới nhất
        except Exception as e_hist:
            print(f"DB_ERROR in get_chat_history: {type(e_hist).__name__} - {e_hist}")
            import traceback
            traceback.print_exc()
            return []

    async def send_chat_history(self):
        try:
            history = await self.get_chat_history()
            if history is None: # Nếu get_chat_history trả về None do lỗi
                print("send_chat_history: History is None, not sending.")
                return

            print(f"send_chat_history: Sending {len(history)} historical messages.")
            for msg_data in history:
                await self.send(text_data=json.dumps({
                    'message': msg_data['content'],
                    'sender_id': msg_data['sender__id'],
                    'sender_username': msg_data['sender__username'],
                    # Chuyển đổi datetime object thành string nếu nó chưa phải là string
                    'timestamp': msg_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(msg_data['timestamp'], 'strftime') else str(msg_data['timestamp']),
                    'is_history': True
                }))
        except Exception as e_send_hist:
            print(f"ERROR in send_chat_history: {type(e_send_hist).__name__} - {e_send_hist}")
            import traceback
            traceback.print_exc()