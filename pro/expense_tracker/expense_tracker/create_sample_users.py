from app import create_app
from models import db, User

def create_sample_users():
    app = create_app()
    with app.app_context():
        # Create admin user
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@example.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)

        # Create customer user
        customer = User.query.filter_by(username='customer').first()
        if not customer:
            customer = User(username='customer', email='customer@example.com', role='customer')
            customer.set_password('customer123')
            db.session.add(customer)

        db.session.commit()
        print("Sample users created successfully!")
        print("\nAdmin User Credentials:")
        print("Username: admin")
        print("Password: admin123")
        print("\nCustomer User Credentials:")
        print("Username: customer")
        print("Password: customer123")

if __name__ == '__main__':
    create_sample_users()