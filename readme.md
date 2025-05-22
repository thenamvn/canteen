**Canteen - Online Food Delivery Platform**

![image](https://github.com/user-attachments/assets/301729cb-a129-4938-80af-db58cc223864)

**🍔 Overview**

Canteen is a modern, Django-based web application for online food ordering and delivery management. The platform connects food sellers with customers, offering a seamless experience for browsing, ordering, and managing food items.

**✨ Features**

**For Customers**

*   **User Authentication** - Secure login system with customized user profiles
*   **Product Browsing** - Browse through categorized food items with pagination
*   **Shopping Cart** - Add items to cart and modify quantities before checkout
*   **Order Management** - Track order status and view order history
*   **User Profile** - Manage personal information and delivery addresses
*   **Online Payment** - Secure payment processing via PayOS integration
*   **Real-time Chat** - Communicate directly with sellers
**For Sellers**

*   **Product Management** - Add, edit, and delete food items
*   **Order Processing** - View and manage received orders
*   **Availability Control** - Toggle product availability status
*   **Real-time Chat Management** - View and respond to customer inquiries via a dedicated chat interface
*   **Seller Profile Management** - Update shop information and logo


**For Administrators**

*   **Category Management** - Create and organize product categories
*   **User Management** - Manage both customers and sellers
*   **Complete System Control** - Access to all platform features

**🛠️ Tech Stack**

*   **Backend**: Django 5.1.3, Django Channels (for WebSockets)
*   **Database**: MySQL
*   **Frontend**: HTML5, CSS3, Tailwind CSS
*   **Channel Layer**: Redis (for Django Channels)
*   **Media Storage**: Local file system
*   **Payment Gateway**: PayOS SDK
*   **Authentication**: Django's built-in authentication system with custom User model

**📋 Prerequisites**

*   Python 3.8+
*   MySQL Server
*   pip

**🚀 Installation**

**1\. Clone the Repository**
```bash
git clone https://github.com/yourusername/canteen.git
cd canteen
```
### 2\. Install Dependencies
```bash
pip install -r requirements.txt
```
### 4\. Configure Database

Create a MySQL database and update the settings in [settings.py](vscode-file://vscode-app/c:/Users/Administrator/AppData/Local/Programs/Microsoft%20VS%20Code/resources/app/out/vs/code/electron-sandbox/workbench/workbench.html):
```
DATABASES \= {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'canteen\_db',
        'USER': 'your\_username',
        'PASSWORD': 'your\_password',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'init\_command': "SET sql\_mode='STRICT\_TRANS\_TABLES'",
        },
    }
}
```
Alternatively, create a `.env` file in the project root and add your database configuration:
```
DB\_NAME=canteen\_db
DB\_USER=your\_username
DB\_PASSWORD=your\_password
DB\_HOST=localhost
DB\_PORT=3306
```
### 
5\. Setup Redis for real-time chat  
**Using Docker:**
```bash
docker run --name redis-server -p 6379:6379 -d redis
```
**Use unofficial Redis build for Windows:**
- Downdload zip form https://github.com/tporadowski/redis 
- Extract it and run the redis-server.exe file
```bash
redis-server.exe
```
- Open another terminal and run:
```bash
redis-cli.exe
```
###
6\. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```
### 

7\. Create a Superuser
```bash
python manage.py createsuperuser
```
### 

8\. Collect Static Files
```bash
python manage.py collectstatic
```
### 

9\. Run the Development Server
```bash
python -m daphne -p 8001 canteen.asgi:application
```
Visit [http://127.0.0.1:8001/](vscode-file://vscode-app/c:/Users/Administrator/AppData/Local/Programs/Microsoft%20VS%20Code/resources/app/out/vs/code/electron-sandbox/workbench/workbench.html) or any port you defined (-p 8001) in your browser to access the application.

## 📂 Project Structure
```
canteen/

├── canteen/            # Project configuration files

├── cart/               # Shopping cart functionality

├── media/              # Uploaded media files

├── orders/             # Order management

├── products/           # Product catalog and management

├── static/             # Static files (CSS, JS, images)

├── staticfiles/        # Collected static files

├── templates/          # Base templates

└── users/              # User authentication and profiles
```
## 

🧩 Key Components

### Models

*   **User** - Extended Django user with seller capabilities and profile ([users/models.py](users/models.py))
*   **Product** - Food items with details, pricing, and availability ([products/models.py](products/models.py))
*   **Category** - Hierarchical product categorization ([products/models.py](products/models.py))
*   **Cart** - Session-based user shopping cart functionality ([cart/cart.py](cart/cart.py))
*   **Order/OrderItem** - Order processing, history, and payment details ([orders/models.py](orders/models.py))
*   **Address** - User delivery addresses ([users/models.py](users/models.py))
*   **ChatRoom/ChatMessage** - Models for managing real-time chat sessions and messages between users and sellers ([chat/models.py](chat/models.py))
*   **SellerProfile** - Dedicated profile for sellers to manage shop details ([users/models.py](users/models.py))


### Views

*   **HomeView** - Landing page with product listing ([products/views.py](products/views.py))
*   **CategoryProductsView** - Products filtered by category with sorting ([products/views.py](products/views.py))
*   **ProductDetailView** - Detailed product view, including customer chat initiation ([products/views.py](products/views.py))
*   **CartView** - Shopping cart management ([cart/views.py](cart/views.py))
*   **CheckoutView** - Order finalization, address selection/creation, and payment method selection ([orders/views.py](orders/views.py))
*   **Order Views** - Customer order list, order detail, PayOS payment handling (return, cancel, webhook) ([orders/views.py](orders/views.py))
*   **SellerDashboard** - Seller product management ([products/views.py](products/views.py))
*   **Seller Order Views** - Seller-specific order list and detail views ([orders/views.py](orders/views.py))
*   **Seller Chat Views** - List of chat rooms and individual chat room interface for sellers ([chat/views.py](chat/views.py))
*   **User Profile Views** - Customer profile, address management, seller profile editing ([users/views.py](users/views.py))

### Core Logic

*   **Payment Integration**: Utilizes PayOS SDK for online payments, handling payment link creation, return/cancel URLs, and webhooks for status updates ([orders/views.py](orders/views.py)).
*   **Real-time Chat**: Implemented using Django Channels and WebSockets, with Redis as the channel layer. Separate consumer logic for customer and seller interactions ([chat/consumers.py](chat/consumers.py)).
*   **Address Management**: Users can add, edit, and select delivery addresses during checkout or from their profile.
*   **Order Status Flow**: Comprehensive order status management (e.g., `pending_payment`, `processing`, `shipped`, `delivered`, `cancelled`, `payment_failed`).


## 🖥️ Screenshots

![image](https://github.com/user-attachments/assets/7ca006f8-7f31-4f4e-bc2e-b131014581a6)


_Browse food items from various categories_

![image](https://github.com/user-attachments/assets/028574c1-2831-47d0-b09e-e3354aee433e)


_View detailed product information_

![image](https://github.com/user-attachments/assets/143bef37-8a7e-4b88-890e-9c0c72640eab)


_Manage your shopping cart_

![image](https://github.com/user-attachments/assets/5d23a480-6092-49bd-b431-487676c144c0)


_Seller's product management interface_

## 🔄 Workflow

1.  **Customers** browse products by category or search, and can sort them.
2.  **Customers** view product details and can initiate a real-time chat with the **Seller**.
3.  **Customers** add products to cart.
4.  **Customers** proceed to checkout, select/add a delivery address, and choose a payment method (COD or PayOS).
5.  If PayOS is chosen, the **Customer** is redirected to the PayOS gateway to complete payment.
6.  **Sellers** receive new orders and can view them in their dashboard.
7.  **Sellers** manage conversations with **Customers** through their chat interface.
8.  **Sellers** process orders, updating their status (e.g., processing, shipped).
9.  **Customers** track order status in their profile.
10. System handles payment confirmations and failures via PayOS webhooks and return URLs.

## 🌟 Acknowledgments

*   Tailwind CSS for the sleek, responsive design
*   Django community for the robust framework
*   All contributors who have dedicated time to improve this platform

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📬 Contact

For questions or feedback, please contact us at:

*   Email: [ntnhacker1@gmail.com](vscode-file://vscode-app/c:/Users/Administrator/AppData/Local/Programs/Microsoft%20VS%20Code/resources/app/out/vs/code/electron-sandbox/workbench/workbench.html)
*   GitHub: (https://github.com/thenamvn)
