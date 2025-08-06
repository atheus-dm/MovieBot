from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()  # 👈 Загружает переменные из .env

client = MongoClient(os.getenv("MONGO_URI"))  # 👈 Безопасное получение данных
db = client[os.getenv("MONGO_DB")]
collection = db[os.getenv("MONGO_COLLECTION")]

def log_search(search_type: str, params: dict, results_count: int):
    # ✨ Нормализация user_id — убираем строку, offset и т.п.
    normalized_params = {k: v for k, v in params.items() if k != "offset"}
    if "user_id" in normalized_params:
        try:
            normalized_params["user_id"] = int(normalized_params["user_id"])
        except ValueError:
            pass

    collection.insert_one({
        "timestamp": datetime.utcnow(),
        "search_type": search_type,
        "params": normalized_params,
        "results_count": results_count
    })

def get_recent_logs(user_id: int, limit: int = 10):
    return list(collection.find(
        {"params.user_id": user_id}
    ).sort("timestamp", -1).limit(limit))

def get_top_queries(limit: int = 5):
    pipeline = [
        # 🧠 Группируем по search_type + нормализованные params
        {"$group": {
            "_id": {
                "search_type": "$search_type",
                "params": "$params"
            },
            "count": {"$sum": 1},
            "last_used": {"$max": "$timestamp"}
        }},
        {"$sort": {"count": -1, "last_used": -1}},
        {"$limit": limit},
        {"$project": {
            "_id": "$_id.params",         # 👈 возвращаем только params
            "search_type": "$_id.search_type",  # 👈 добавляем search_type отдельно
            "count": 1,
            "last_used": 1
        }}
    ]
    return list(collection.aggregate(pipeline))



