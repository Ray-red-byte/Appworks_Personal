import json
import pymysql
import pymongo
import logging
from datetime import datetime

from dotenv import load_dotenv
import os
import boto3
import re
from botocore.exceptions import NoCredentialsError

dotenv_path = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/.env'
load_dotenv(dotenv_path)

log_filename = 'log_file.log'
log_file_path = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/log/log_file_good_info_insert.log'
logger = logging.getLogger(__name__)

logging.basicConfig(filename=log_file_path, level=logging.INFO)


# Mongo atlas
CONNECTION_STRING = os.getenv("MONGO_ATLAS_USER")
client = pymongo.MongoClient(CONNECTION_STRING)

# Select a database and collection
db = client["personal_project"]
collection = db["house"]

# S3 setting
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
aws_secret_access_key = os.getenv("S3_SECRET_ACCESS_KEY")
aws_access_key_id = os.getenv("S3_ACCESS_KEY")
aws_bucket = os.getenv("S3_BUCKET_NAME")
s3_good_info_path = 'personal_project/house_detail/good_details/rent_good_info.json'
#s3_good_url_path = 'personal_project/urls/good_urls/rent_good_url.json'
local_good_info_file = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/data/rent_good_info.json'
#local_good_url_file = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/data/rent_good_url.json'


good_json_file_path = "/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/data/rent_good_info.json"


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
    data = collection.find({}, {"h_url": 1})
    if data:
        return data
    return []

def insert_good_info_to_mgdb(good_info_url, info):

    try:
        transform_info_dict = {
            "h_url": good_info_url,
            "h_title": info["house_code"],
            "h_price": float(info["price"].replace(',', '')),
            "h_address": info["address"],
            "h_type": info["type"],
            "h_usage": "None",
            "h_age": int(re.search(r'\d+', info["屋齡"]).group()),
            "h_face": "None",
            "h_env": info["管理方式"],
            "h_size": float(re.search(r'\d+', info["size"]).group()),
            "h_short_stay": info["最短租期"],
            "h_cook": True if info["開伙"] == "可" else False,  # Changed "None" to False
            "h_move_date": info["move_date"],
            "h_pet": info["養寵物"],
            "h_fee_contain": True if info["other_fees"] else False,  # Changed "None" to False
            "h_gender": info["性別限制"],
            "h_deposit": -1,
            "h_identy": info["身分要求"],
            "h_stay_landlord": True if info["與房東同住"] == "不用與房東同住" else False,
            "h_park": True if "有" in info["車位"] else False,
            "h_equip": info["設備"],
            "h_furniture": info["家具"],
            "h_floor": info["floor"],
            "h_corner": True if info["邊間"] == "是" else False,
            "h_center": True if info["中庭"] == "是" else False,
            "h_top_add": True if info["頂樓加蓋"] == "是" else False,
            "h_img_url": info["img_url"],
            "h_layout": info["layout"]
        }


        collection.insert_one(transform_info_dict)

        # Close the connection
        client.close()
        print("Data inserted successfully.")

    except Exception as e:
        # Rollback in case of any error
        print("Error:", e)




def main():

    download_from_s3(aws_bucket, s3_good_info_path, local_good_info_file)
    all_h_url = get_all_mgdb_good_info()
    all_h_url = [doc["h_url"] for doc in all_h_url]

    good_infos = load_from_json(good_json_file_path)
    

    # Log start time
    logger.info(f"Previous number : {len(all_h_url)}")
    timestamp_start = datetime.datetime.now()
    timestamp_start_stf = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"---------- ---Start Crawler {timestamp_start_stf}-------------")

    for good_info_url, content in good_infos.items():

        if good_info_url in all_h_url:
            print("Already in DB. Skip.")
            break

        insert_good_info_to_mgdb(good_info_url, content)

    # Log end time
    logger.info(f"Total number : {len(all_h_url)}")
    timestamp_end = datetime.datetime.now()
    timestamp_end_stf = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"-------------Time consume {timestamp_end - timestamp_start}-------------")
    logger.info(f"-------------End Crawler {timestamp_end_stf}-------------")
    
    
if __name__ == "__main__":
    main()