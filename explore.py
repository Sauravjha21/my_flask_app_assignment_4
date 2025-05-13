from flaskapp import app, db 
from flaskapp.models import UkData  

with app.app_context():
    # Print the table schema
    print("UkData Table Schema:")
    for column in UkData.__table__.columns:
        print(f"- {column.name}: {column.type}")
    
    # Count total records
    count = UkData.query.count()
    print(f"\nTotal records: {count}")
    
    # Print a few sample records
    print("\nSample data (5 records):")
    samples = UkData.query.limit(5).all()
    for sample in samples:
        print("-" * 50)
        for column in UkData.__table__.columns:
            value = getattr(sample, column.name)
            print(f"{column.name}: {value}")