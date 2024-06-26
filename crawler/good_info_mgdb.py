import json
import pymysql
import pymongo
import logging
import datetime

from dotenv import load_dotenv
import os
import boto3
import re
from botocore.exceptions import NoCredentialsError
from user_model.house_data_process import transform_one_house, transform_all_house, get_value_from_house_dict, one_hot_gender


dotenv_path = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/.env'
load_dotenv(dotenv_path)

log_filename = os.getenv("LOG_FILE_NAME")
log_file_path = os.getenv("LOG_FILE_GOOD_INSERT_PATH")
logger = logging.getLogger(__name__)

logging.basicConfig(filename=log_file_path, level=logging.INFO)


# Mongo atlas
CONNECTION_STRING = os.getenv("MONGO_ATLAS_USER")
client = pymongo.MongoClient(CONNECTION_STRING)

# Select a database and collection
db = client["personal_project"]
house_collection = db["house"]
transform_house_collection = db["transform_all_house"]

# S3 setting
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
aws_secret_access_key = os.getenv("S3_SECRET_ACCESS_KEY")
aws_access_key_id = os.getenv("S3_ACCESS_KEY")
aws_bucket = os.getenv("S3_BUCKET_NAME")
s3_good_info_path = os.getenv("S3_GOOD_INFO_PATH")
# s3_good_url_path = 'personal_project/urls/good_urls/rent_good_url.json'
local_good_info_file = os.getenv("LOCAL_GOOD_INFO_FILE")
# local_good_url_file = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/data/rent_good_url.json'


local_good_info_file = os.getenv("LOCAL_GOOD_INFO_FILE")


def load_from_json(json_file):
    try:
        with open(json_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(e)
        return {}


def download_from_s3(bucket_name, s3_path, local_file):
    s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id,
                      aws_secret_access_key=aws_secret_access_key)
    try:
        s3.download_file(bucket_name, s3_path, local_file)
    except Exception as e:
        print(e)
        return False

    return True


def get_all_mgdb_good_info():
    collection = db["house"]
    data = collection.find({}, {"url": 1})
    if data:
        return data
    return []


def get_next_house_id():
    # Find and update the user_id counter
    counter_doc = client['personal_project']['house'].counters.find_one_and_update(
        {"_id": "house_id"},
        {"$inc": {"seq": 1}},
        upsert=True,  # Create the counter if it doesn't exist
        return_document=True
    )
    return counter_doc["seq"]


def insert_good_info_to_mgdb(good_info_url, info):

    try:
        house_id = get_next_house_id()
        transform_info_dict = {
            "id": house_id,
            "url": good_info_url,
            "title": info["house_code"],
            "price": float(info["price"].replace(',', '')),
            "address": info["address"],
            "type": info["type"],
            "usage": "None",
            "age": int(re.search(r'\d+', info["屋齡"]).group()) if info.get("屋齡") else "None",
            "face": "None",
            "env": info["管理方式"],
            "size": float(re.search(r'\d+', info["size"]).group()),
            "short_stay": info["最短租期"],
            # Changed "None" to False
            "cook": True if info["開伙"] == "可" else False,
            "move_date": info["move_date"],
            "pet": info["養寵物"],
            # Changed "None" to False
            "fee_contain": True if info["other_fees"] else False,
            "gender": info["性別限制"],
            "deposit": -1,
            "identy": info["身分要求"],
            "stay_landlord": True if info["與房東同住"] == "不用與房東同住" else False,
            "park": True if "有" in info["車位"] else False,
            "equip": info["設備"],
            "furniture": info["家具"],
            "floor": info["floor"],
            "corner": True if info["邊間"] == "是" else False,
            "center": True if info["中庭"] == "是" else False,
            "top_add": True if info["頂樓加蓋"] == "是" else False,
            "img_url": info["img_url"],
            "layout": info["layout"],
            'updated_at': datetime.datetime.now()
        }

        house_collection.insert_one(transform_info_dict)

        # Transform into value
        row, house_dict = transform_one_house(transform_info_dict)
        transform_house_collection.insert_one(house_dict)

        # Close the connection
        client.close()
        print("Data inserted successfully.")

    except Exception as e:
        # Rollback in case of any error
        print(info)
        print("Error:", e)


def main():

    download_from_s3(aws_bucket, s3_good_info_path, local_good_info_file)
    all_h_url = get_all_mgdb_good_info()
    all_h_url = [doc["url"] for doc in all_h_url]

    good_infos = load_from_json(good_json_file_path)
    print(len(all_h_url))

    # Log start time
    logger.info(f"Previous number : {len(all_h_url)}")
    timestamp_start = datetime.datetime.now()
    timestamp_start_stf = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(
        f"---------- ---Start Crawler {timestamp_start_stf}-------------")

    for good_info_url, content in good_infos.items():

        if good_info_url in all_h_url:
            print("Already in DB. Skip.")
            break

        insert_good_info_to_mgdb(good_info_url, content)

    client.close()

    # Log end time
    logger.info(f"Total number : {len(all_h_url)}")
    timestamp_end = datetime.datetime.now()
    timestamp_end_stf = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(
        f"-------------Time consume {timestamp_end - timestamp_start}-------------")
    logger.info(f"-------------End Crawler {timestamp_end_stf}-------------")


if __name__ == "__main__":
    main()
