import json
import pymongo
from dotenv import load_dotenv
from datetime import datetime
import os
import re
import logging
import boto3
from botocore.exceptions import NoCredentialsError


dotenv_path = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/.env'
load_dotenv(dotenv_path)

# Mongo atlas
CONNECTION_STRING = os.getenv("MONGO_ATLAS_USER")
client = pymongo.MongoClient(CONNECTION_STRING)

# Select a database and collection
db = client["personal_project"]
collection = db["house"]

# logging
log_file_path = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/log/log_file_hap_info_insert.log'
logger = logging.getLogger(__name__)

logging.basicConfig(filename=log_file_path, level=logging.INFO)


# S3 setting
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
aws_secret_access_key = os.getenv("S3_SECRET_ACCESS_KEY")
aws_access_key_id = os.getenv("S3_ACCESS_KEY")
aws_bucket = os.getenv("S3_BUCKET_NAME")
s3_hap_info_path = 'personal_project/house_detail/good_details/rent_hap_info.json'
s3_hap_url_path = 'personal_project/urls/good_urls/rent_good_url.json'
local_hap_info_file = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/data/rent_hap_info.json'
local_hap_url_file = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/data/rent_hap_url.json'


hap_json_file_path = "/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/data/rent_hap_info.json"


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


def get_all_mgdb_info():
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


def insert_hap_info_to_mgdb(good_info_url, info):

    try:

        house_id = get_next_house_id()
        transform_info_dict = {
            "id": house_id,
            "url": good_info_url,
            "title": info["house_code"],
            "price": float(re.search(r'\d+', info["price"].replace(',', '')).group()),
            "address": info["address"],
            "type": info["類型"],
            "usage": info["法定用途"],
            "age": int(re.search(r'\d+', info["屋齡"]).group()) if info.get("屋齡") else "None",
            "face": info["朝向"] if info.get("朝向") else "None",
            "env": info["物件環境"] if info.get("物件環境") else "None",
            "size": float(re.search(r'\d+', info["坪數"]).group()),
            "short_stay": info["最短租期"] if info.get("最短租期") else "None",
            "cook": True if info.get("開伙") and info["開伙"] == "可" else False,
            "move_date": info["可遷入日"] if info.get("可遷入日") else "None",
            "pet": info["飼養寵物"] if info.get("飼養寵物") else "None",
            "fee_contain": True if info.get("租金內含") else "None",
            "gender": info["性別限制"] if info.get("性別限制") else "None",
            "deposit": -1,
            "identy": info["身分要求"] if info.get("身分要求") else "None",
            "stay_landlord": True if info.get("房東同住") and info["房東同住"] == "是" else False,
            "park": True if "有" in info["車位"] else False,
            "equip": info["設備"] if info.get("設備") else "None",
            "furniture": info["傢俱"] if info.get("傢俱") else "None",
            "floor": info["樓層/樓高"],
            "corner": info["邊間"] if info.get("邊間") and info["邊間"] == "是" else False,
            "center": info["中庭"] if info.get("中庭") and info["中庭"] == "是" else False,
            "top_add": info["頂樓加蓋"] if info.get("頂樓加蓋") and info["頂樓加蓋"] == "是" else False,
            "img_url": info["img_url"],
            "layout": info["格局"],
            "'updated_at'": datetime.now()
        }

        collection.insert_one(transform_info_dict)

        # Close the connection
        client.close()
        print("Data inserted successfully.")

    except Exception as e:
        # Rollback in case of any error
        print("Error:", e)


def main():

    # download info files from S3
    download_from_s3(aws_bucket, s3_hap_info_path, local_hap_info_file)

    # get all urls from mongoDB
    all_h_url = get_all_mgdb_info(collection)
    all_h_url = [doc["url"] for doc in all_h_url]
    print(len(all_h_url))

    hap_infos = load_from_json(hap_json_file_path)

    # Log start time
    logger.info(f"Previous number : {len(all_h_url)}")
    timestamp_start = datetime.now()
    timestamp_start_stf = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(
        f"---------- ---Start Crawler {timestamp_start_stf}-------------")

    for hap_info_url, content in hap_infos.items():

        if hap_info_url in all_h_url:
            print("Already in DB. Skip.")
            break

        insert_hap_info_to_mgdb(hap_info_url, content)

    # Log end time
    logger.info(f"Total number : {len(all_h_url)}")
    timestamp_end = datetime.now()
    timestamp_end_stf = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(
        f"-------------Time consume {timestamp_end - timestamp_start}-------------")
    logger.info(f"-------------End Crawler {timestamp_end_stf}-------------")


if __name__ == "__main__":
    main()
