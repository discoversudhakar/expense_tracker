from functools import wraps

# Decorator for admin-only routes
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or getattr(current_user, 'role', 'customer') != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, Expense, Category, User
from forms import ExpenseForm, CategoryForm, LoginForm, RegistrationForm, AdminUserForm
from config import Config
from datetime import datetime, date, timedelta
from sqlalchemy import func, extract
from functools import wraps
import calendar

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    with app.app_context():
        try:
            db.create_all()
            
            # Create default categories if none exist
            if not Category.query.first():
                default_categories = [
                    ('Food & Dining', '#FF6B6B'),
                    ('Transportation', '#4ECDC4'),
                    ('Shopping', '#45B7D1'),
                    ('Entertainment', '#96CEB4'),
                    ('Bills & Utilities', '#FECA57'),
                    ('Healthcare', '#FF9FF3'),
                    ('Education', '#54A0FF'),
                    ('Travel', '#5F27CD'),
                    ('Other', '#00D2D3')
                ]
                
                for name, color in default_categories:
                    if not Category.query.filter_by(name=name).first():
                        category = Category(name=name, color=color)
                        db.session.add(category)
                db.session.commit()
        except Exception as e:
            print(f"Error during initialization: {e}")
            db.session.rollback()
    
    return app

app = create_app()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('dashboard')
        return redirect(next_page)
    return render_template('login.html', form=form)

@app.route('/admin/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_create_user():
    form = AdminUserForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, role=form.role.data)
        user.set_password(form.password.data)
        try:
            db.session.add(user)
            db.session.commit()
            flash(f'User {user.username} has been created successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {str(e)}', 'error')
    return render_template('admin_user_form.html', form=form, title='Create New User')

@app.route('/')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
        
    try:
        # Get current month expenses
        today = datetime.now()
        current_month = today.month
        current_year = today.year
        start_of_month = datetime(current_year, current_month, 1)
        # Calculate end of month
        if current_month == 12:
            end_of_month = datetime(current_year + 1, 1, 1) - timedelta(days=1)
        else:
            end_of_month = datetime(current_year, current_month + 1, 1) - timedelta(days=1)
        
        monthly_expenses_result = db.session.query(func.sum(Expense.amount)).filter(
            Expense.date >= start_of_month,
            Expense.date <= end_of_month,
            Expense.user_id == current_user.id
        ).scalar()
        monthly_expenses = float(monthly_expenses_result) if monthly_expenses_result else 0.0
        
        # Get recent expenses (last 10) and convert to dictionaries
        # Get recent expenses and convert to dictionaries using the model's to_dict method
        recent_expenses_query = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.created_at.desc()).limit(10).all()
        recent_expenses = []
        for expense in recent_expenses_query:
            try:
                recent_expenses.append(expense.to_dict())
            except Exception as e:
                print(f"Error processing expense {expense.id}: {e}")
        
        # Get category-wise expenses - COMPLETELY FIXED
        category_query_results = db.session.query(
            Category.name,
            Category.color,
            func.sum(Expense.amount)
        ).join(Expense, Expense.category == Category.name).filter(
            Expense.date >= start_of_month,
            Expense.date <= end_of_month,
            Expense.user_id == current_user.id
        ).group_by(Category.name, Category.color).all()
        
        # Convert to plain Python list - NO SQLAlchemy objects
        category_expenses = []
        for result in category_query_results:
            category_name = str(result[0])  # Category name
            category_color = str(result[1])  # Category color
            total_amount = float(result[2]) if result[2] else 0.0  # Sum of expenses
            category_expenses.append([category_name, total_amount, category_color])
        
        # Get daily expenses - COMPLETELY FIXED
        end_date = datetime.now()
        start_date = end_date - timedelta(days=6)
        
        # Convert dates for query
        query_start_date = start_date.date()
        query_end_date = end_date.date()
        print(f"Query date range: {query_start_date} to {query_end_date}")  # Debug log
        
        daily_query_results = db.session.query(
            Expense.date,
            func.sum(Expense.amount)
        ).filter(
            Expense.date >= query_start_date,
            Expense.date <= query_end_date
        ).group_by(Expense.date).all()
        
        # Convert to dictionary first
        daily_data_dict = {}
        for result in daily_query_results:
            try:
                expense_date = result[0]  # First element is date
                print(f"Query result date: {expense_date}, type: {type(expense_date)}")  # Debug log
                if isinstance(expense_date, str):
                    # Convert string date to date object
                    expense_date = datetime.strptime(expense_date, '%Y-%m-%d').date()
                elif isinstance(expense_date, datetime):
                    expense_date = expense_date.date()
                total_amount = float(result[1]) if result[1] else 0.0  # Second element is sum
                daily_data_dict[expense_date] = total_amount
            except Exception as e:
                print(f"Error processing query result: {e}, data: {result}")  # Debug log
        
        # Create complete 7-day list with plain Python data
        daily_expenses = []
        current_date = start_date.date()
        end_date_date = end_date.date()
        while current_date <= end_date_date:
            try:
                date_str = current_date.strftime('%Y-%m-%d') if isinstance(current_date, (datetime, date)) else current_date
                print(f"Processing date: {current_date}, type: {type(current_date)}")  # Debug log
                daily_expenses.append({
                    'date': date_str,
                    'amount': daily_data_dict.get(current_date, 0.0)
                })
            except Exception as e:
                print(f"Error processing date {current_date}: {e}")  # Debug log
            current_date += timedelta(days=1)
        
        return render_template('index.html',
                             monthly_total=monthly_expenses,
                             recent_expenses=recent_expenses,
                             category_expenses=category_expenses,
                             daily_expenses=daily_expenses,
                             current_month=calendar.month_name[current_month])
    
    except Exception as e:
        print(f"Error in dashboard: {e}")
        # Return dashboard with empty data if error occurs
        return render_template('index.html',
                             monthly_total=0.0,
                             recent_expenses=[],
                             category_expenses=[],
                             daily_expenses=[],
                             current_month=calendar.month_name[datetime.now().month])

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    form = ExpenseForm()
    
    # Set default date to today
    if not form.date.data:
        form.date.data = date.today()
    
    if form.validate_on_submit():
        try:
            # Convert form.date.data to date object if it's datetime
            expense_date = form.date.data
            if isinstance(expense_date, datetime):
                expense_date = expense_date.date()
            
            expense = Expense(
                amount=float(form.amount.data),  # Ensure amount is float
                category=form.category.data,
                description=form.description.data.strip() if form.description.data else None,
                date=expense_date,
                user_id=current_user.id
            )
            
            db.session.add(expense)
            db.session.commit()
            
            flash('Expense added successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding expense: {str(e)}', 'error')
            return redirect(url_for('add_expense'))
    
    return render_template('add_expense.html', form=form)

@app.route('/expenses')
@login_required
def expenses():
    page = request.args.get('page', 1, type=int)
    category_filter = request.args.get('category', '')
    
    # Admin sees all expenses, others see only their own
    if current_user.role == 'admin':
        query = Expense.query
    else:
        query = Expense.query.filter_by(user_id=current_user.id)
    
    if category_filter:
        query = query.filter(Expense.category == category_filter)
    
    expenses = query.order_by(Expense.date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    categories = [choice[0] for choice in ExpenseForm().category.choices]
    
    return render_template('expenses.html', 
                         expenses=expenses, 
                         categories=categories,
                         current_category=category_filter)

@app.route('/delete_expense/<int:id>', methods=['POST'])
@login_required
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    # Only admin or owner can delete
    if current_user.role != 'admin' and expense.user_id != current_user.id:
        flash('You do not have permission to delete this expense.', 'error')
        return redirect(url_for('expenses'))
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('expenses'))

@app.route('/edit_expense/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_expense(id):
    expense = Expense.query.get_or_404(id)
    # Only admin or owner can edit
    if current_user.role != 'admin' and expense.user_id != current_user.id:
        flash('You do not have permission to edit this expense.', 'error')
        return redirect(url_for('expenses'))
    form = ExpenseForm(obj=expense)
    if form.validate_on_submit():
        expense.amount = form.amount.data
        expense.category = form.category.data
        expense.description = form.description.data
        expense.date = form.date.data
        db.session.commit()
        flash('Expense updated successfully!', 'success')
        return redirect(url_for('expenses'))
    return render_template('add_expense.html', form=form, expense=expense)

@app.route('/api/monthly_data')
def monthly_data():
    """API endpoint for monthly expense data"""
    current_year = datetime.now().year
    
    # Filter by user_id if not admin
    query = db.session.query(func.sum(Expense.amount))
    if not current_user.is_authenticated or current_user.role != 'admin':
        query = query.filter(Expense.user_id == current_user.id)
    
    monthly_data = []
    for month in range(1, 13):
        total = query.filter(
            extract('month', Expense.date) == month,
            extract('year', Expense.date) == current_year
        ).scalar()
        
        monthly_data.append({
            'month': calendar.month_name[month][:3],
            'amount': float(total) if total else 0.0
        })
    
    return jsonify(monthly_data)

# Admin routes
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    # Get statistics
    total_users = User.query.count()
    total_expenses = db.session.query(func.sum(Expense.amount)).scalar() or 0
    total_categories = Category.query.count()
    
    # Get monthly expenses
    current_month = datetime.now().month
    current_year = datetime.now().year
    monthly_expenses = db.session.query(func.sum(Expense.amount)).filter(
        extract('month', Expense.date) == current_month,
        extract('year', Expense.date) == current_year
    ).scalar() or 0
    
    # Get users with their total expenses
    users = User.query.all()
    for user in users:
        user.total_expenses = db.session.query(func.sum(Expense.amount)).filter(
            Expense.user_id == user.id
        ).scalar() or 0
    
    return render_template('admin_dashboard.html',
                         total_users=total_users,
                         total_expenses=total_expenses,
                         total_categories=total_categories,
                         monthly_expenses=monthly_expenses,
                         users=users)

@app.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_user():
    form = AdminUserForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'User {user.username} has been created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_user_form.html', form=form, title='Add New User')

@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = AdminUserForm(obj=user)
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash(f'User {user.username} has been updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_user_form.html', form=form, user=user, title='Edit User')

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    if current_user.id == user_id:
        flash('You cannot delete your own account!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} has been deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

# Category Management Routes
@app.route('/categories')
@login_required
@admin_required
def manage_categories():
    categories = Category.query.order_by(Category.name).all()
    return render_template('categories.html', categories=categories)

@app.route('/categories/add', methods=['POST'])
@login_required
@admin_required
def add_category():
    name = request.form.get('name')
    color = request.form.get('color')
    
    if not name or not color:
        flash('Category name and color are required.', 'error')
        return redirect(url_for('manage_categories'))
    
    # Check if category already exists
    if Category.query.filter_by(name=name).first():
        flash('A category with this name already exists.', 'error')
        return redirect(url_for('manage_categories'))
    
    category = Category(name=name, color=color)
    db.session.add(category)
    try:
        db.session.commit()
        flash('Category added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding category: {str(e)}', 'error')
    
    return redirect(url_for('manage_categories'))

@app.route('/categories/edit', methods=['POST'])
@login_required
@admin_required
def edit_category():
    category_id = request.form.get('category_id')
    name = request.form.get('name')
    color = request.form.get('color')
    
    if not all([category_id, name, color]):
        flash('All fields are required.', 'error')
        return redirect(url_for('manage_categories'))
    
    category = Category.query.get_or_404(category_id)
    
    # Check if new name already exists (excluding current category)
    existing = Category.query.filter(Category.name == name, Category.id != category.id).first()
    if existing:
        flash('A category with this name already exists.', 'error')
        return redirect(url_for('manage_categories'))
    
    category.name = name
    category.color = color
    
    try:
        db.session.commit()
        flash('Category updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating category: {str(e)}', 'error')
    
    return redirect(url_for('manage_categories'))

@app.route('/categories/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    
    # Update all expenses using this category to 'Uncategorized'
    uncategorized = Category.query.filter_by(name='Uncategorized').first()
    if not uncategorized:
        uncategorized = Category(name='Uncategorized', color='#999999')
        db.session.add(uncategorized)
        db.session.flush()
    
    Expense.query.filter_by(category=category.name).update({'category': 'Uncategorized'})
    
    try:
        db.session.delete(category)
        db.session.commit()
        flash('Category deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting category: {str(e)}', 'error')
    
    return redirect(url_for('manage_categories'))

if __name__ == '__main__':
    app.run(debug=True)
