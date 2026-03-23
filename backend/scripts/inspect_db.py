import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, select, func
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("No DATABASE_URL found in .env")
    exit(1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

metadata = MetaData()
metadata.reflect(bind=engine)

print("="*60)
print("DATABASE TABLES REVIEW")
print("="*60)

for table_name in metadata.tables:
    table = metadata.tables[table_name]
    count = session.execute(select(func.count()).select_from(table)).scalar()
    print(f"- {table_name}: {count} rows")
    
    if count > 0:
        print(f"  Sample row from '{table_name}':")
        try:
            sample_row = session.execute(select(table).limit(1)).fetchone()
            if sample_row:
                for col_name, val in zip(sample_row._mapping.keys(), sample_row):
                    # truncate long strings for better printing
                    val_str = str(val)
                    if len(val_str) > 50:
                        val_str = val_str[:47] + "..."
                    print(f"    {col_name}: {val_str}")
        except Exception as e:
            print(f"    Error reading sample row: {e}")
    print()

print("="*60)
session.close()
