import sqlite3
import json

db_path = 'instance/poe2_trade.db'

def query_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables: {tables}")
    
    # Search for Charms in analysis_result
    cursor.execute("SELECT * FROM analysis_result WHERE base_type LIKE '%Charm%';")
    results = cursor.fetchall()
    print(f"Analysis Results for Charms: {len(results)}")
    for row in results:
        print(row)
        
    # Search for Charms in modifiers
    cursor.execute("SELECT m.* FROM modifier m JOIN analysis_result a ON m.analysis_id = a.id WHERE a.base_type LIKE '%Charm%';")
    modifiers = cursor.fetchall()
    print(f"Modifiers for Charms: {len(modifiers)}")
    for row in modifiers:
        print(row)
        
    conn.close()

if __name__ == "__main__":
    query_db()
