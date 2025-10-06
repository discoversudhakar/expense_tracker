from app import create_app
from models import db

def upgrade_database():
    app = create_app()
    with app.app_context():
        # Add role column to user table
        with db.engine.connect() as conn:
            conn.execute(db.text('ALTER TABLE user ADD COLUMN role VARCHAR(20) DEFAULT "customer"'))
            conn.commit()
        print("Database upgraded successfully!")

if __name__ == '__main__':
    upgrade_database()