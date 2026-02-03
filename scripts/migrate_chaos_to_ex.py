from pymongo import MongoClient
import os
from dotenv import load_dotenv

def migrate():
    load_dotenv()
    # Default to localhost if MONGODB_URI is not set
    uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/poe2_trade')
    
    print(f"Connecting to MongoDB at: {uri}")
    client = MongoClient(uri)
    
    # Extract database name from URI or use default
    # If the URI contains a database name (e.g., .../poe2_trade), MongoClient might handle it,
    # but let's be explicit if possible.
    db_name = uri.split('/')[-1].split('?')[0] if '/' in uri else 'poe2_trade'
    if not db_name:
        db_name = 'poe2_trade'
        
    db = client.get_database(db_name)
    print(f"Using database: {db_name}")

    # 1. Rename top-level fields
    print("Renaming top-level fields in 'analysis_result'...")
    rename_op = {
        '$rename': {
            'normal_avg_chaos': 'normal_avg_ex',
            'crafting_avg_chaos': 'crafting_avg_ex',
            'magic_avg_chaos': 'magic_avg_ex',
            'gap_chaos': 'gap_ex'
        }
    }
    
    result = db.analysis_result.update_many({}, rename_op)
    print(f"Top-level field rename completed. Matched: {result.matched_count}, Modified: {result.modified_count}")

    # 2. Rename embedded fields in 'modifiers' array
    # MongoDB $rename does NOT support array elements directly.
    # We must loop for modifiers.
    print("Migrating embedded 'modifiers' fields...")
    cursor = db.analysis_result.find({'modifiers.price_chaos': {'$exists': True}})
    
    count = 0
    for doc in cursor:
        updated_mods = []
        changed = False
        for mod in doc.get('modifiers', []):
            if 'price_chaos' in mod:
                mod['price_ex'] = mod.pop('price_chaos')
                changed = True
            updated_mods.append(mod)
        
        if changed:
            db.analysis_result.update_one(
                {'_id': doc['_id']}, 
                {'$set': {'modifiers': updated_mods}}
            )
            count += 1
            if count % 10 == 0:
                print(f"Processed {count} documents...")

    print(f"Migration finished. Total documents with updated modifiers: {count}")
    client.close()

if __name__ == "__main__":
    migrate()
