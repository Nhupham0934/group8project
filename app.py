# app.py
from flask import render_template, redirect, request, session, url_for, Flask, jsonify
from flask import send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
import random
import string
from werkzeug.utils import secure_filename

from models import init_app, db
from models.user import User
from models.cloth_type import ClothType
from models.product import Product
from models.product_size import ProductSize
from models.order import Order
from models.order_item import OrderItem
from models.review import Review

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_KEY_PREFIX'] = 'helloo'
app.config['SESSION_COOKIE_NAME'] = 'Bookstorevsession'
app.secret_key = "Kc5c3zTk'-3<&BdL:P92O{_(:-NkY+KM"

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
init_app(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form['role']

        if password != confirm_password:
            error = 'Passwords do not match.'
        else:
            from models.user import User  # Adjust import as needed
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                error = 'Email is already registered.'
            else:
                new_user = User(
                    username=username,
                    email=email,
                    password=password,  # 👈 No hashing
                    role=role,
                    created_at=datetime.now()
                )
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('login'))

    return render_template('register.html', error=error)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']

        from models.user import User  # Adjust as needed
        user = User.query.filter_by(email=email, password=password).first()

        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role

            if user.role == 'admin':
                return redirect('/admin/dashboard')
            else:
                return redirect('/user/dashboard')
        else:
            error = 'Invalid email or password.'

    return render_template('login.html', error=error)


@app.route('/user/dashboard')
def user_dashboard():
    if 'user_id' not in session or session.get('role') != 'customer':
        return redirect('/login')
    return render_template('user/dashboard.html')


@app.route('/get_products')
def get_products():
    from models.product import Product
    from models.cloth_type import ClothType
    from models.product_size import ProductSize
    from sqlalchemy import func

    products = Product.query.all()
    product_data = []

    for p in products:
        # Manually get cloth_type name
        cloth_type = ClothType.query.filter_by(id=p.cloth_type_id).first()
        cloth_type_name = cloth_type.type_name if cloth_type else "N/A"

        # Get total stock from ProductSize table
        total_stock = db.session.query(func.sum(ProductSize.stock)) \
                          .filter(ProductSize.product_id == p.id).scalar() or 0

        product_data.append({
            'id': p.id,
            'name': p.name,
            'price': p.price,
            'image_url': p.image_url,
            'cloth_type': cloth_type_name,
            'total_stock': total_stock
        })

    return jsonify(product_data)


# ---------------- Users ----------------
@app.route('/register', methods=['POST'])
def create_user():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')

    if not username or not email or not password or not role:
        return jsonify({"message": "Missing required fields"}), 400

    user = User(
        username=username,
        email=email,
        password=password,
        role=role,
        created_at=datetime.now()
    )
    try:
        db.session.add(user)
        db.session.commit()
        db.session.close()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error creating user", "error": str(e)}), 400
    return jsonify({"message": "User created successfully."}), 201


@app.route('/get_users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{k: v for k, v in u.__dict__.items() if not k.startswith('_')} for u in users])


@app.route('/product_details/<int:product_id>')
def product_details(product_id):
    # Get product
    product = Product.query.filter_by(id=product_id).first()
    if not product:
        return "Product not found", 404

    # Get cloth type manually
    cloth_type = ClothType.query.filter_by(id=product.cloth_type_id).first()

    # Get available sizes for this product
    sizes = ProductSize.query.filter_by(product_id=product.id).all()

    # Get reviews with usernames
    reviews = db.session.query(Review, User.username).join(User, Review.user_id == User.id) \
        .filter(Review.product_id == product.id).all()

    formatted_reviews = [{
        'username': username,
        'rating': review.rating,
        'comment': review.comment
    } for review, username in reviews]

    return render_template(
        'user/product_details.html',
        product=product,
        cloth_type=cloth_type,
        sizes=sizes,
        reviews=formatted_reviews,
        is_admin=(session.get('role') == 'admin')
    )


@app.route('/get_product_sizes')
def get_product_sizes():
    from models.product_size import ProductSize
    from models.product import Product

    sizes = ProductSize.query.all()
    response = []

    for size in sizes:
        product = Product.query.filter_by(id=size.product_id).first()
        response.append({
            'product_id': size.product_id,
            'product_name': product.name if product else "Unknown",
            'size_label': size.size_label,
            'stock': size.stock
        })

    return jsonify(response)


@app.route('/add_order', methods=['POST'])
def add_order():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    new_order = Order(
        user_id=session['user_id'],
        order_date=datetime.now(),
        total_amount=float(data['total_amount']),
        status='Pending'
    )
    db.session.add(new_order)
    db.session.commit()

    return jsonify({'order_id': new_order.id})


@app.route('/add_order_items', methods=['POST'])
def add_order_items():
    data = request.get_json()
    order_id = data['order_id']
    items = data['items']

    for item in items:
        # Get product price
        product = Product.query.get(item['product_id'])
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # Insert order item with actual price
        new_item = OrderItem(
            order_id=order_id,
            product_id=item['product_id'],
            size_label=item['size_label'],
            quantity=item['quantity'],
            price=product.price  # ✅ fixed here
        )
        db.session.add(new_item)

        # Update stock
        size_entry = ProductSize.query.filter_by(
            product_id=item['product_id'],
            size_label=item['size_label']
        ).first()

        if size_entry and size_entry.stock >= item['quantity']:
            size_entry.stock -= item['quantity']
        else:
            return jsonify({'error': f'Not enough stock for {item["size_label"]}'}), 400

    db.session.commit()
    return jsonify({'success': True})


@app.route('/cart')
def cart():
    if 'user_id' not in session or session.get('role') != 'customer':
        return redirect('/login')
    return render_template('user/cart.html')


@app.route('/orders')
def orders():
    if 'user_id' not in session or session.get('role') != 'customer':
        return redirect('/login')
    return render_template('user/orders.html')


@app.route('/get_orders')
def get_orders():
    if 'user_id' not in session:
        return jsonify([])

    orders = Order.query.filter_by(user_id=session['user_id']).order_by(Order.order_date.desc()).all()

    data = [{
        'id': o.id,
        'status': o.status,
        'order_date': o.order_date.strftime('%Y-%m-%d %H:%M:%S'),
        'total_amount': o.total_amount
    } for o in orders]

    return jsonify(data)


@app.route('/get_order_details/<int:order_id>')
def get_order_details(order_id):
    from models.order import Order
    from models.order_item import OrderItem
    from models.product import Product

    if 'user_id' not in session:
        return redirect('/login')

    order = Order.query.get_or_404(order_id)

    if session['role'] == 'customer' and order.user_id != session['user_id']:
        return "Unauthorized", 403

    order_items = OrderItem.query.filter_by(order_id=order.id).all()
    item_details = []

    for item in order_items:
        product = Product.query.get(item.product_id)
        item_details.append({
            'product_id': product.id,
            'name': product.name,
            'image_url': product.image_url,
            'quantity': item.quantity,
            'price': item.price,
            'size_label': item.size_label
        })

    return render_template(
        'user/order_details.html',
        order=order,
        items=item_details
    )


@app.route('/cancel_order', methods=['POST'])
def cancel_order():
    from models.order import Order
    from models.order_item import OrderItem
    from models.product_size import ProductSize

    if 'user_id' not in session or session.get('role') != 'customer':
        return redirect('/login')

    order_id = request.form.get('order_id')
    order = Order.query.filter_by(id=order_id, user_id=session['user_id']).first()

    if order and order.status.lower().strip() == 'pending':
        order.status = 'Cancelled'

        # restore stock
        items = OrderItem.query.filter_by(order_id=order.id).all()
        for item in items:
            size = ProductSize.query.filter_by(product_id=item.product_id, size_label=item.size_label).first()
            if size:
                size.stock += item.quantity

        db.session.commit()

    return redirect(f'/get_order_details/{order_id}')


@app.route('/admin/cancel_order', methods=['POST'])
def admin_cancel_order():
    from models.order import Order
    from models.order_item import OrderItem
    from models.product_size import ProductSize

    if session.get('role') != 'admin':
        return redirect('/login')

    order_id = request.form.get('order_id')
    order = Order.query.get(order_id)

    if order and order.status == 'Pending':
        order.status = 'Cancelled'

        # Restore stock
        order_items = OrderItem.query.filter_by(order_id=order.id).all()
        for item in order_items:
            size = ProductSize.query.filter_by(product_id=item.product_id, size_label=item.size_label).first()
            if size:
                size.stock += item.quantity

        db.session.commit()

    return redirect(f'/get_order_details/{order_id}')


@app.route('/admin/mark_delivered', methods=['POST'])
def admin_mark_delivered():
    from models.order import Order

    if session.get('role') != 'admin':
        return redirect('/login')

    order_id = request.form.get('order_id')
    order = Order.query.get(order_id)

    if order and order.status == 'Pending':
        order.status = 'Delivered'
        db.session.commit()

    return redirect(f'/get_order_details/{order_id}')


@app.route('/admin/delete_product', methods=['POST'])
def delete_product():
    from models.product import Product
    from models.product_size import ProductSize

    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    product_id = request.form.get('product_id')
    if not product_id:
        return redirect('/admin/products')

    # Delete related sizes first
    ProductSize.query.filter_by(product_id=product_id).delete()

    # Then delete the product
    product = Product.query.get(product_id)
    if product:
        db.session.delete(product)

    db.session.commit()
    return redirect('/admin/products')


@app.route('/admin/update_stock', methods=['POST'])
def update_stock():
    from models.product_size import ProductSize

    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    product_id = request.form.get('product_id')
    if not product_id:
        return redirect('/admin/products')

    # Loop through expected sizes
    for size_label in ['S', 'M', 'L', 'XL']:
        stock_field = f'size_{size_label}'
        if stock_field in request.form:
            stock_value = int(request.form[stock_field])

            size_entry = ProductSize.query.filter_by(product_id=product_id, size_label=size_label).first()

            if size_entry:
                size_entry.stock = stock_value
            else:
                # Create size entry if it doesn't exist
                new_size = ProductSize(
                    product_id=product_id,
                    size_label=size_label,
                    stock=stock_value
                )
                db.session.add(new_size)

    db.session.commit()
    return redirect(f'/product_details/{product_id}')


@app.route('/admin/users')
def admin_users():
    from models.user import User

    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@app.route('/admin/delete_user', methods=['POST'])
def admin_delete_user():
    from models.user import User

    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    user_id = request.form.get('user_id')
    user = User.query.get(user_id)

    if user:
        db.session.delete(user)
        db.session.commit()

    return redirect('/admin/users')


@app.route('/admin/orders')
def admin_orders():
    from models.order import Order

    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    orders = Order.query.order_by(Order.order_date.desc()).all()
    return render_template('admin/orders.html', orders=orders)


@app.route('/admin/cloth_types', methods=['GET', 'POST'])
def admin_cloth_types():
    from models.cloth_type import ClothType

    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    error_message = None

    if request.method == 'POST':
        type_name = request.form.get('type_name')
        description = request.form.get('description', '')

        if not type_name.strip():
            error_message = "Type name is required."
        else:
            # Optional: Prevent duplicate type names
            existing = ClothType.query.filter_by(type_name=type_name.strip()).first()
            if existing:
                error_message = f"Cloth type '{type_name}' already exists."
            else:
                new_type = ClothType(type_name=type_name.strip(), description=description.strip())
                db.session.add(new_type)
                db.session.commit()
                return redirect('/admin/cloth_types')

    cloth_types = ClothType.query.order_by(ClothType.id.desc()).all()
    return render_template('admin/cloth_types.html', cloth_types=cloth_types, error_message=error_message)


@app.route('/admin/delete_cloth_type', methods=['POST'])
def delete_cloth_type():
    from models.cloth_type import ClothType

    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    cloth_type_id = request.form.get('cloth_type_id')
    cloth_type = ClothType.query.get(cloth_type_id)

    if cloth_type:
        db.session.delete(cloth_type)
        db.session.commit()

    return redirect('/admin/cloth_types')



# ---------------- Cloth Types ----------------
@app.route('/add_cloth_type', methods=['POST'])
def add_cloth_type():
    type_name = request.form.get('type_name')
    description = request.form.get('description')

    cloth_type = ClothType(
        type_name=type_name,
        description=description
    )
    try:
        db.session.add(cloth_type)
        db.session.commit()
        db.session.close()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error creating cloth type", "error": str(e)}), 400
    return jsonify({"message": "Cloth type added successfully."}), 201


@app.route('/get_cloth_types', methods=['GET'])
def get_cloth_types():
    types = ClothType.query.all()
    return jsonify([{k: v for k, v in t.__dict__.items() if not k.startswith('_')} for t in types])


# # ---------------- Products ----------------
# @app.route('/add_product', methods=['POST'])
# def add_product():
#     name = request.form.get('name')
#     description = request.form.get('description')
#     price = request.form.get('price')
#     cloth_type_id = request.form.get('cloth_type_id')
#     color = request.form.get('color')
#     created_by = request.form.get('created_by')
#     file = request.files.get('image_url')
#
#     image_url = None
#     if file and file.filename != '':
#         filename = secure_filename(file.filename)
#         filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         file.save(filepath)
#         image_url = filepath
#
#     product = Product(
#         name=name,
#         description=description,
#         price=price,
#         cloth_type_id=cloth_type_id,
#         color=color,
#         image_url=image_url,
#         created_by=created_by,
#         created_at=datetime.now()
#     )
#     try:
#         db.session.add(product)
#         db.session.commit()
#         db.session.close()
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({"message": "Error adding product", "error": str(e)}), 400
#     return jsonify({"message": "Product added successfully."}), 201


# @app.route('/get_products', methods=['GET'])
# def get_products():
#     products = Product.query.all()
#     return jsonify([{k: v for k, v in p.__dict__.items() if not k.startswith('_')} for p in products])
#

# ---------------- Product Sizes ----------------
@app.route('/add_product_size', methods=['POST'])
def add_product_size():
    product_id = request.form.get('product_id')
    size_label = request.form.get('size_label')
    stock = request.form.get('stock')

    size = ProductSize(
        product_id=product_id,
        size_label=size_label,
        stock=stock
    )
    try:
        db.session.add(size)
        db.session.commit()
        db.session.close()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error adding product size", "error": str(e)}), 400
    return jsonify({"message": "Product size added successfully."}), 201


@app.route('/submit_review', methods=['POST'])
def submit_review():
    from models.review import Review
    from datetime import datetime

    if 'user_id' not in session or session.get('role') != 'customer':
        return redirect('/login')

    user_id = session['user_id']
    product_id = request.form.get('product_id')
    rating = int(request.form.get('rating'))
    comment = request.form.get('comment')

    new_review = Review(
        user_id=user_id,
        product_id=product_id,
        rating=rating,
        comment=comment,
        review_date=datetime.now()
    )
    db.session.add(new_review)
    db.session.commit()

    return redirect(request.referrer or '/orders')


@app.route('/set_order_delivered', methods=['POST'])
def set_order_delivered():
    from models.order import Order

    order_id = request.form.get('order_id')
    order = Order.query.get(order_id)

    if not order:
        return jsonify({'error': 'Order not found'}), 404

    order.status = 'Delivered'
    db.session.commit()
    return jsonify({'message': f'Order #{order.id} marked as Delivered'})


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')
    return render_template('admin/dashboard.html')


@app.route('/admin/get_orders')
def admin_get_orders():
    from models.order import Order
    if session.get('role') != 'admin':
        return jsonify([])

    orders = Order.query.order_by(Order.order_date.desc()).all()
    return jsonify([{
        'id': o.id,
        'total_amount': o.total_amount
    } for o in orders])


@app.route('/admin/get_users')
def admin_get_users():
    from models.user import User
    if session.get('role') != 'admin':
        return jsonify([])

    users = User.query.all()
    return jsonify([{
        'id': u.id,
        'role': u.role
    } for u in users])


@app.route('/admin/products')
def admin_products():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    from models.product import Product
    from models.product_size import ProductSize
    from models.cloth_type import ClothType

    products = Product.query.all()
    result = []

    for p in products:
        cloth_type = ClothType.query.filter_by(id=p.cloth_type_id).first()
        stock = db.session.query(db.func.sum(ProductSize.stock)) \
                    .filter_by(product_id=p.id).scalar() or 0

        result.append({
            'id': p.id,
            'name': p.name,
            'image_url': p.image_url,
            'price': p.price,
            'cloth_type': cloth_type.type_name if cloth_type else "Unknown",
            'total_stock': stock
        })

    return render_template('admin/products.html', products=result)


import os
from werkzeug.utils import secure_filename
from datetime import datetime


@app.route('/admin/add_product', methods=['GET', 'POST'])
def add_product():
    from models.product import Product
    from models.product_size import ProductSize
    from models.cloth_type import ClothType

    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        color = request.form.get('color', '')
        price = float(request.form['price'])
        cloth_type_id = int(request.form['cloth_type_id'])

        # Handle image upload
        image_file = request.files.get('image')
        image_url = ''
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            image_path = os.path.join('uploads', filename)
            image_file.save(image_path)
            image_url = image_path

        # Insert product
        new_product = Product(
            name=name,
            description=description,
            price=price,
            cloth_type_id=cloth_type_id,
            color=color,
            image_url=image_url,
            created_by=session['user_id'],
            created_at=datetime.now()
        )
        db.session.add(new_product)
        db.session.commit()

        # Add size-based stock
        for size_label in ['S', 'M', 'L', 'XL']:
            stock = int(request.form.get(f'size_{size_label}', 0))
            if stock > 0:
                db.session.add(ProductSize(
                    product_id=new_product.id,
                    size_label=size_label,
                    stock=stock
                ))

        db.session.commit()
        return redirect('/admin/products')

    # On GET request: show form
    cloth_types = ClothType.query.all()
    return render_template('admin/add_product.html', cloth_types=cloth_types)


# ---------------- Get Order Items ----------------
@app.route('/get_order_items', methods=['POST'])
def get_order_items():
    order_id = request.form.get('order_id')

    if not order_id:
        return jsonify({"error": "order_id is required"}), 400

    items = OrderItem.query.filter_by(order_id=order_id).all()
    item_list = [
        {
            "id": item.id,
            "order_id": item.order_id,
            "product_id": item.product_id,
            "size_label": item.size_label,
            "quantity": item.quantity,
            "price": item.price
        } for item in items
    ]
    return jsonify(item_list), 200


# ---------------- Reviews ----------------
@app.route('/add_review', methods=['POST'])
def add_review():
    user_id = request.form.get('user_id')
    product_id = request.form.get('product_id')
    rating = request.form.get('rating')
    comment = request.form.get('comment')

    review = Review(
        user_id=user_id,
        product_id=product_id,
        rating=rating,
        comment=comment,
        review_date=datetime.now()
    )
    try:
        db.session.add(review)
        db.session.commit()
        db.session.close()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error adding review", "error": str(e)}), 400
    return jsonify({"message": "Review added successfully."}), 201


@app.route('/get_reviews', methods=['GET'])
def get_reviews():
    reviews = Review.query.all()
    return jsonify([{k: v for k, v in r.__dict__.items() if not k.startswith('_')} for r in reviews])


if __name__ == '__main__':
    app.run(debug=True)
