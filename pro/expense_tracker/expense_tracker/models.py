from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='customer')  # 'admin' or 'customer'
    expenses = db.relationship('Expense', backref='user', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), db.ForeignKey('category.name'), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, **kwargs):
        if 'date' not in kwargs:
            kwargs['date'] = datetime.utcnow().date()
        elif isinstance(kwargs['date'], str):
            kwargs['date'] = datetime.strptime(kwargs['date'], '%Y-%m-%d').date()
        elif isinstance(kwargs['date'], datetime):
            kwargs['date'] = kwargs['date'].date()
        super(Expense, self).__init__(**kwargs)
    
    # Relationship with Category
    category_info = db.relationship('Category', backref=db.backref('expenses', lazy=True))
    
    def __repr__(self):
        return f'<Expense {self.amount} - {self.category}>'
    
    def format_date(self):
        """Format the date safely"""
        try:
            if isinstance(self.date, (datetime, date)):
                return self.date.strftime('%Y-%m-%d')
            elif isinstance(self.date, str):
                return self.date
            return str(self.date)
        except Exception as e:
            print(f"Error formatting date: {e}")
            return str(self.date)

    def to_dict(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'category': self.category,
            'description': self.description,
            'date': self.format_date(),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if isinstance(self.created_at, datetime) else str(self.created_at)
        }

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    color = db.Column(db.String(7), default='#007bff')  # Hex color code
    
    def __repr__(self):
        return f'<Category {self.name}>'
