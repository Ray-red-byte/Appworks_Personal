import json
from faker import Faker
import random
from dotenv import load_dotenv
import pymongo
import os
from Appworks_Personal.function import calculate_active_status

fake = Faker()


dotenv_path = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/.env'
load_dotenv(dotenv_path)

# Mongo atlas
CONNECTION_STRING = os.getenv("MONGO_ATLAS_USER")
client = pymongo.MongoClient(CONNECTION_STRING)


def update_user_active_status():
    db = client["personal_project"]
    user_collection = db["user"]

    for user in user_collection.find():
        be_cancel = len(user.get("be_cancel", []))
        be_chatted_user = user["be_chatted_user"]
        chat_user = user["chat_user"]
        saved_house = len(user.get('saved_house', []))
        click_house = len(user.get("click_house", []))

        active_status = calculate_active_status(
            be_cancel, be_chatted_user, chat_user, saved_house, click_house)

        user_collection.update_one({"user_id": user["user_id"]},
                                   {"$set":
                                    {
                                        "active_status": active_status
                                    }
                                    },
                                   upsert=False
                                   )
        print("update user status")


def update_user_cancel_status():
    db = client["personal_project"]
    user_collection = db["user"]

    for user in user_collection.find():
        be_cancel_count = user_collection.find_one(
            {"user_id": user["user_id"]})["be_cancel"]
        be_cancel_user_ls = random.sample(range(2139, 3139), be_cancel_count)

        user_collection.update_one({"user_id": user["user_id"]},
                                   {"$set":
                                    {
                                        "be_cancel": be_cancel_user_ls
                                    }
                                    },
                                   upsert=True
                                   )
        print("update user status")


def update_user_status():
    db = client["personal_project"]
    user_collection = db["user"]

    for user in user_collection.find():
        be_cancel_count = random.randint(0, 100)

        if be_cancel_count > 50:
            chat_user_count = random.randint(0, 10)
            be_chatted_user_count = random.randint(0, 10)
        elif be_cancel_count < 50 and be_cancel_count > 30:
            chat_user_count = random.randint(10, 20)
            be_chatted_user_count = random.randint(10, 20)
        elif be_cancel_count < 30 and be_cancel_count > 10:
            chat_user_count = random.randint(20, 30)
            be_chatted_user_count = random.randint(20, 30)

        user_collection.update_one({"user_id": user["user_id"]},
                                   {"$set":
                                    {
                                        "be_cancel": be_cancel_count,
                                        "chat_user": chat_user_count,
                                        "be_chatted_user": be_chatted_user_count
                                    }
                                    },
                                   upsert=False
                                   )
        print("update user status")


def get_fake_user():
    db = client["personal_project"]
    user_collection = db["user"]

    for user in user_collection.find():

        be_cancel_count = random.randint(0, 100)

        if be_cancel_count > 50:
            chat_user_count = random.randint(0, 10)
            be_chatted_user_count = random.randint(0, 10)
        elif be_cancel_count < 50 and be_cancel_count > 30:
            chat_user_count = random.randint(10, 20)
            be_chatted_user_count = random.randint(10, 20)
        elif be_cancel_count < 30 and be_cancel_count > 10:
            chat_user_count = random.randint(20, 30)
            be_chatted_user_count = random.randint(20, 30)

        user = user_collection.find_one({"user_id": user["user_id"]})
        user["be_cancel"] = be_cancel_count
        user["chat_user"] = chat_user_count
        user["be_chatted_user"] = be_chatted_user_count

        print(user)


# print(get_fake_user())

'''
with open("/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/data/fake_userstatus.json", "w") as f:
    json.dump(fake_users, f, ensure_ascii=False)
'''

update_user_active_status()
