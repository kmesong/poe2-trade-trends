import sqlite3
import os

def migrate():
    db_path = 'instance/poe2_trade.db'
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found. Nothing to migrate.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(analysis_result)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'crafting_avg_chaos' not in columns:
            print("Adding crafting_avg_chaos column to analysis_result table...")
            cursor.execute("ALTER TABLE analysis_result ADD COLUMN crafting_avg_chaos FLOAT DEFAULT 0.0")
            conn.commit()
            print("Migration successful.")
        else:
            print("Column crafting_avg_chaos already exists.")

    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
