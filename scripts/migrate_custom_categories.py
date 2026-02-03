import sqlite3
import os

def migrate():
    # Database is located in instance/poe2_trade.db relative to project root
    # Since this script is in scripts/, we need to go up one level
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'poe2_trade.db')
    
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path))
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print(f"Updating database at {db_path}...")
        print("Creating custom_category table if it doesn't exist...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custom_category (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255) UNIQUE NOT NULL,
                items TEXT NOT NULL
            )
        """)
        
        # Create index on name if it doesn't exist
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_custom_category_name ON custom_category (name)")
        
        conn.commit()
        print("Migration successful: custom_category table is ready.")

    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
