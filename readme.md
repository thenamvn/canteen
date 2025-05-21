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

**For Sellers**

*   **Product Management** - Add, edit, and delete food items
*   **Order Processing** - View and manage received orders
*   **Availability Control** - Toggle product availability status

**For Administrators**

*   **Category Management** - Create and organize product categories
*   **User Management** - Manage both customers and sellers
*   **Complete System Control** - Access to all platform features

**🛠️ Tech Stack**

*   **Backend**: Django 5.1.3
*   **Database**: MySQL
*   **Frontend**: HTML5, CSS3, Tailwind CSS (via CDN)
*   **Media Storage**: Local file system
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

5\. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```
### 

6\. Create a Superuser
```bash
python manage.py createsuperuser
```
### 

7\. Collect Static Files
```bash
python manage.py collectstatic
```
### 

8\. Run the Development Server
```bash
python manage.py runserver
```
Visit [http://127.0.0.1:8000/](vscode-file://vscode-app/c:/Users/Administrator/AppData/Local/Programs/Microsoft%20VS%20Code/resources/app/out/vs/code/electron-sandbox/workbench/workbench.html) in your browser to access the application.

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

*   **User** - Extended Django user with seller capabilities
*   **Product** - Food items with details, pricing, and availability
*   **Category** - Hierarchical product categorization
*   **Cart** - User shopping cart functionality
*   **Order/OrderItem** - Order processing and history
*   **Address** - User delivery addresses

### Views

*   **HomeView** - Landing page with product listing
*   **CategoryProductsView** - Products filtered by category
*   **ProductDetailView** - Detailed product view
*   **CartView** - Shopping cart management
*   **CheckoutView** - Order finalization
*   **SellerDashboard** - Seller product management

## 🖥️ Screenshots

<img alt="Homepage" src="https://via.placeholder.com/800x450/ffffff/333333?text=Homepage">

_Browse food items from various categories_

<img alt="Product Detail" src="https://via.placeholder.com/800x450/ffffff/333333?text=Product+Detail">

_View detailed product information_

<img alt="Shopping Cart" src="https://via.placeholder.com/800x450/ffffff/333333?text=Shopping+Cart">

_Manage your shopping cart_

<img alt="Seller Dashboard" src="https://via.placeholder.com/800x450/ffffff/333333?text=Seller+Dashboard">

_Seller's product management interface_

## 🔄 Workflow

1.  **Customers** browse products by category or search
2.  **Customers** add products to cart
3.  **Customers** checkout and place orders
4.  **Sellers** receive and process orders
5.  **Customers** track order status

## 🌟 Acknowledgments

*   Tailwind CSS for the sleek, responsive design
*   Django community for the robust framework
*   All contributors who have dedicated time to improve this platform

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Contributors

*   [Your Name](vscode-file://vscode-app/c:/Users/Administrator/AppData/Local/Programs/Microsoft%20VS%20Code/resources/app/out/vs/code/electron-sandbox/workbench/workbench.html) - Project Lead & Developer

## 📬 Contact

For questions or feedback, please contact us at:

*   Email: [your.email@example.com](vscode-file://vscode-app/c:/Users/Administrator/AppData/Local/Programs/Microsoft%20VS%20Code/resources/app/out/vs/code/electron-sandbox/workbench/workbench.html)
*   GitHub: [Your GitHub Profile](vscode-file://vscode-app/c:/Users/Administrator/AppData/Local/Programs/Microsoft%20VS%20Code/resources/app/out/vs/code/electron-sandbox/workbench/workbench.html)
