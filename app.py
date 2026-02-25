import os
from flask import Flask, render_template, url_for, flash, redirect, request, abort
from models import db, User, Product, Cart, Order
from forms import RegistrationForm, LoginForm, ProductForm
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['UPLOAD_FOLDER'] = 'static/images'

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables
with app.app_context():
    db.create_all()
    # Create a dummy admin if it doesn't exist
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@example.com', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

    # Add dummy products if database is empty
    if not Product.query.first():
        p1 = Product(name='Modern Headset', description='High-quality noise-canceling wireless headphones.', price=199.99, category='Electronics', image='https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=400&q=80')
        p2 = Product(name='Smart Watch', description='Stylish smartwatch with health tracking features.', price=249.50, category='Electronics', image='https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=400&q=80')
        p3 = Product(name='Travel Backpack', description='Durable and spacious backpack for all your adventures.', price=79.00, category='Fashion', image='https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=400&q=80')
        p4 = Product(name='Classic Sneakers', description='Comfortable and trendy sneakers for everyday wear.', price=120.00, category='Fashion', image='https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=400&q=80')
        db.session.add_all([p1, p2, p3, p4])
        db.session.commit()

@app.route("/")
@app.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category')
    search = request.args.get('q')
    
    query = Product.query
    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(Product.name.contains(search) | Product.description.contains(search))
    
    products_pagination = query.paginate(page=page, per_page=4)
    categories = db.session.query(Product.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('index.html', products=products_pagination.items, pagination=products_pagination, categories=categories)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

# --- Product & Admin Routes ---
@app.route("/admin", methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        abort(403)
    form = ProductForm()
    if form.validate_on_submit():
        image_file = 'default_product.jpg'
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            # Ensure upload folder exists
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
            form.image.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_file = filename
        
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            category=form.category.data,
            image=image_file
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    products = Product.query.all()
    return render_template('admin_dashboard.html', form=form, products=products)

@app.route("/product/delete/<int:product_id>", methods=['POST'])
@login_required
def delete_product(product_id):
    if not current_user.is_admin:
        abort(403)
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted!', 'info')
    return redirect(url_for('admin_dashboard'))

# --- Shopping Cart Routes ---
@app.route("/add_to_cart/<int:product_id>", methods=['POST'])
@login_required
def add_to_cart(product_id):
    cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = Cart(user_id=current_user.id, product_id=product_id)
        db.session.add(cart_item)
    db.session.commit()
    flash('Added to cart!', 'success')
    return redirect(url_for('home'))

@app.route("/cart")
@login_required
def cart():
    items = Cart.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in items)
    return render_template('cart.html', items=items, total=total)

@app.route("/cart/remove/<int:item_id>")
@login_required
def remove_from_cart(item_id):
    item = Cart.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        abort(403)
    db.session.delete(item)
    db.session.commit()
    flash('Removed from cart', 'info')
    return redirect(url_for('cart'))

@app.route("/checkout")
@login_required
def checkout():
    items = Cart.query.filter_by(user_id=current_user.id).all()
    if not items:
        flash('Cart is empty', 'warning')
        return redirect(url_for('home'))
    total = sum(item.product.price * item.quantity for item in items)
    return render_template('checkout.html', items=items, total=total)

@app.route("/place_order", methods=['POST'])
@login_required
def place_order():
    items = Cart.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in items)
    order = Order(user_id=current_user.id, total_amount=total)
    db.session.add(order)
    # Clear cart
    Cart.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('Order placed successfully!', 'success')
    return render_template('success.html')

# --- REST API ---
@app.route("/api/products")
def get_products_api():
    products = Product.query.all()
    output = []
    for product in products:
        product_data = {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'category': product.category,
            'image_url': product.image if product.image.startswith('http') else url_for('static', filename='images/' + product.image, _external=True)
        }
        output.append(product_data)
    return {"products": output}

if __name__ == '__main__':
    app.run(debug=True)
