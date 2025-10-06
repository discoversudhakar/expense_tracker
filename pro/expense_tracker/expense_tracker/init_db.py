from app import create_app
from models import db, User, Category

def init_db():
    app = create_app()
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create admin user if it doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Create default categories
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
        
        try:
            db.session.commit()
            print("Database initialized successfully!")
            print("\nAdmin user created:")
            print("Username: admin")
            print("Password: admin123")
        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()

if __name__ == '__main__':
    init_db()