from pymongo import MongoClient

uri = "mongodb://<username>:<password>@localhost:27017/"
client = MongoClient(uri)

try:
    database = client.get_database("focusbuddy")
    bl_collection = database.get_collection("block_list")

    query = {"domain": "https://facebook.com"}
    blocked_site = bl_collection.find_one(query)

    print(blocked_site)

    user_collection = database["user"]
    result = user_collection.insert_one({"user_id": 2, "user_status": 4})
    print(result.acknowledged)

    client.close()

except Exception as e:
    raise Exception("Unable to find the document due to the following error: ", e)
