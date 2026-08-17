import os
from pymongo import MongoClient

uri = os.getenv("MONGO_URI")
if not uri:
    print("MONGO_URI is not configured; Mongo test skipped.")
else:
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        print("✅ Подключение успешно!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
