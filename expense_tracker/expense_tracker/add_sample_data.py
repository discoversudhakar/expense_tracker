from app import create_app
from models import db, Expense, Category, User
from datetime import datetime, timedelta
import random

def add_sample_data():
    app = create_app()
    with app.app_context():
        # Clear existing data
        Expense.query.delete()
        Category.query.delete()
        
        # Create a test user if not exists
        user = User.query.filter_by(username='demo').first()
        if not user:
            user = User(username='demo', email='demo@example.com')
            user.set_password('demo123')
            db.session.add(user)
            db.session.commit()

        # Create categories
        categories = [
            Category(name='Groceries', color='#28a745'),
            Category(name='Transportation', color='#007bff'),
            Category(name='Entertainment', color='#6f42c1'),
            Category(name='Bills', color='#dc3545'),
            Category(name='Shopping', color='#fd7e14'),
            Category(name='Healthcare', color='#20c997'),
            Category(name='Dining Out', color='#e83e8c')
        ]
        
        for category in categories:
            db.session.add(category)
        db.session.commit()

        # Sample expenses for the last 30 days
        expenses = [
            # Groceries
            ('Weekly Groceries', 85.50, categories[0]),
            ('Fresh Produce', 35.20, categories[0]),
            ('Bulk Items Costco', 120.75, categories[0]),
            
            # Transportation
            ('Gas', 45.00, categories[1]),
            ('Bus Pass', 60.00, categories[1]),
            ('Car Maintenance', 150.00, categories[1]),
            
            # Entertainment
            ('Movie Night', 25.00, categories[2]),
            ('Concert Tickets', 80.00, categories[2]),
            ('Netflix Subscription', 15.99, categories[2]),
            
            # Bills
            ('Electricity Bill', 95.50, categories[3]),
            ('Internet Bill', 75.00, categories[3]),
            ('Water Bill', 45.00, categories[3]),
            ('Phone Bill', 60.00, categories[3]),
            
            # Shopping
            ('New Shoes', 89.99, categories[4]),
            ('Clothes Shopping', 120.00, categories[4]),
            ('Electronics', 199.99, categories[4]),
            
            # Healthcare
            ('Pharmacy', 35.00, categories[5]),
            ('Doctor Visit', 50.00, categories[5]),
            
            # Dining Out
            ('Lunch', 12.50, categories[6]),
            ('Dinner with Friends', 45.00, categories[6]),
            ('Coffee Shop', 5.75, categories[6])
        ]

        # Add expenses with different dates over the last 30 days
        today = datetime.now()
        for i, (description, amount, category) in enumerate(expenses):
            date = today - timedelta(days=random.randint(0, 30))
            expense = Expense(
                description=description,
                amount=amount,
                date=date,
                category=category.name,
                user_id=user.id
            )
            db.session.add(expense)

        db.session.commit()
        print("Sample data added successfully!")
        print("\nDemo User Credentials:")
        print("Username: demo")
        print("Password: demo123")

if __name__ == '__main__':
    add_sample_data()