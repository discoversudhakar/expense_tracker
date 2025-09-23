from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, Expense, Category, User
from forms import ExpenseForm, CategoryForm, LoginForm, RegistrationForm
from config import Config
from datetime import datetime, date, timedelta
from sqlalchemy import func, extract
import calendar
import os

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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now registered!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/')
@login_required
def dashboard():
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
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('expenses'))

@app.route('/edit_expense/<int:id>', methods=['GET', 'POST'])
def edit_expense(id):
    expense = Expense.query.get_or_404(id)
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
    
    monthly_data = []
    for month in range(1, 13):
        total = db.session.query(func.sum(Expense.amount)).filter(
            extract('month', Expense.date) == month,
            extract('year', Expense.date) == current_year
        ).scalar()
        
        monthly_data.append({
            'month': calendar.month_name[month][:3],
            'amount': float(total) if total else 0.0
        })
    
    return jsonify(monthly_data)

# 🔥 CRITICAL FIX FOR RENDER DEPLOYMENT 🔥
if __name__ == '__main__':
    # Get port from environment variable (Render sets this automatically)
    port = int(os.environ.get('PORT', 10000))
    # Bind to 0.0.0.0 so Render can detect the port
    app.run(debug=False, host='0.0.0.0', port=port)
