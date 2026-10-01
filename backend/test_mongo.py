"""
Test MongoDB Atlas Connection Utility
Run this script to verify connectivity to your MongoDB Atlas cluster:
    python test_mongo.py
"""
import asyncio
import sys
from app.core.config import settings
from app.core.mongodb import init_mongo, get_mongo_client, get_mongo_db

async def main():
    print("=" * 60)
    print("  VitaLens MongoDB Atlas Connection Diagnostic")
    print("=" * 60)
    
    url = settings.MONGODB_URL
    if not url:
        print("\n[ERROR] MONGODB_URL is not defined in backend/.env")
        print("Please add MONGODB_URL=mongodb+srv://VitaLens:<PASSWORD>@<cluster>.mongodb.net/vitalens_db to backend/.env")
        sys.exit(1)
        
    masked_url = url
    if "@" in url:
        prefix, host = url.split("@", 1)
        masked_url = f"mongodb+srv://VitaLens:****@{host}"
    print(f"\nConfigured URL: {masked_url}")
    print(f"Target Database: {settings.MONGODB_DB_NAME}\n")
    
    if "<PASSWORD>" in url or "<YOUR_PASSWORD" in url or "<password>" in url:
        print("[ACTION REQUIRED] Placeholder '<PASSWORD>' detected!")
        print("Please open backend/.env and replace <PASSWORD> with your actual MongoDB Atlas password.")
        sys.exit(1)
        
    print("Attempting connection to MongoDB Atlas...")
    success = await init_mongo()
    
    if success:
        client = get_mongo_client()
        db = get_mongo_db()
        server_info = await client.server_info()
        print("\n[SUCCESS] Connected to MongoDB Atlas successfully!")
        print(f"  - MongoDB Version: {server_info.get('version')}")
        print(f"  - Database: {db.name}")
        cols = await db.list_collection_names()
        print(f"  - Collections in database: {cols if cols else '(empty - ready for data)'}")
        print("\nYour MongoDB Atlas integration is working properly!\n")
    else:
        print("\n[FAILED] Could not connect to MongoDB Atlas.")
        print("Please check:")
        print("  1. Is the password correct?")
        print("  2. Did you whitelist your current IP address (or 0.0.0.0/0) in MongoDB Atlas Network Access?")
        print("  3. Is the cluster address correct?")

if __name__ == "__main__":
    asyncio.run(main())
