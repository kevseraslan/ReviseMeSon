from app import app, db

# Create an application context
with app.app_context():
    try:
        # Test database connection by creating all tables
        db.create_all()
        print("Database connection successful and tables created.")
    except Exception as e:
        print(f"Error connecting to the database: {e}")