import json
import pymysql
from dotenv import load_dotenv
import os
import boto3
import re
from botocore.exceptions import NoCredentialsError

dotenv_path = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/.env'
load_dotenv(dotenv_path)


# MySQL 
mysql_host = os.getenv("DB_HOST")
mysql_user = os.getenv("DB_USER")
mysql_pwd = os.getenv("DB_PASSWORD")
mysql_db = os.getenv("DB_DATABASE")


# connect to mysql
conn = pymysql.connect(
    host=mysql_host,
    user=mysql_user,
    password=mysql_pwd,
    database=mysql_db
)


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


def get_all_good_info():
    cursor = conn.cursor()
    cursor.execute("SELECT h_url FROM house")
    data = cursor.fetchall()
    if data:
        return data
    return []


def insert_good_info_to_rds(good_info_url, info):

    cursor = conn.cursor()
    try:
        h_url = good_info_url
        h_title = info["house_code"]
        h_price = float(info["price"].replace(',', ''))
        h_address = info["address"]
        h_type = info["type"]
        h_usage = "None"
        h_age = int(re.search(r'\d+', info["屋齡"]).group()) 
        h_face = "None"
        h_env = info["管理方式"]
        h_size = float(re.search(r'\d+\.\d+', info["size"]).group())
        h_short_stay = info["最短租期"]
        h_cook = True if info["開伙"] == "可" else "None"
        h_move_date = info["move_date"]
        h_pet = info["養寵物"] 
        h_fee_contain = True if info["other_fees"] else "None"
        h_gender = info["性別限制"]
        h_deposit = -1
        h_identy = info["身分要求"]
        h_stay_landlord = True if info["與房東同住"] == "不用與房東同住" else False
        
        h_park = True if "有" in info["車位"] else False

        h_equip = True if info["設備"] else False
        h_furniture = True if info["家具"] else False
        h_floor = info["floor"]
        h_corner = True if info["邊間"] == "是" else False
        h_center = True if info["中庭"] == "是" else False
        h_top_add = True if info["頂樓加蓋"] == "是" else False
        h_img_url = info["img_url"]
        h_layout = info["layout"]

        values = (
            h_url, h_title, h_price, h_address, h_type, h_usage, h_age, h_face, h_env, h_size,
            h_short_stay, h_cook, h_move_date, h_pet, h_fee_contain, h_gender, h_deposit, h_identy,
            h_stay_landlord, h_park, h_equip, h_furniture, h_floor, h_corner, h_center, h_top_add, h_img_url,
            h_layout
        )
        
        # Construct the SQL query for insertion
        sql = """
                INSERT INTO house (h_url, h_title, h_price, h_address, h_type, h_usage, h_age, h_face, h_env,
                h_size, h_short_stay, h_cook, h_move_date, h_pet, h_fee_contain, h_gender, h_deposit, h_identy,
                h_stay_landlord, h_park, h_equip, h_furniture, h_floor, h_corner, h_center, h_top_add, h_img_url,
                h_layout) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s);
                """

        # Execute the SQL query
        cursor.execute(sql, values)
        # Commit the changes
        conn.commit()
        print("Data inserted successfully.")

    except Exception as e:
        # Rollback in case of any error
        conn.rollback()
        print("Error:", e)




def main():
    #download_from_s3(aws_bucket, s3_good_info_path, local_good_info_file)
    all_h_url = get_all_good_info()

    test_data = {
        "https://rent.housefun.com.tw/rent/house/1831664/": {
        "house_code": "【捷運中山站】精品宅(房屋編號：CC831664)",
        "price": "45,000",
        "address": "台北市中山區中山北路一段\n租金行情",
        "size": "20.91 坪",
        "other_fees": "管理費|水費|電費",
        "floor": "7 / 14 樓",
        "layout": "1房(室)1廳1衛",
        "type": "電梯大樓",
        "move_date": "隨時",
        "min_stay": "一年",
        "img_url": "https://pic.hfcdn.com/res/DrawImage/ShowPic/400/300/HFRENT07/Z999/541d62cd-f7a3-4baa-b43c-6aa8cbf72112/Z999A00120240000412180244ec840.jpg?t=1805",
        "屋齡": "13年",
        "最短租期": "一年",
        "身分要求": "不限",
        "性別限制": "男女皆可",
        "與房東同住": "不用與房東同住",
        "開伙": "可",
        "養寵物": "不可",
        "管理方式": "--",
        "邊間": "--",
        "中庭": "--",
        "車位": "無",
        "頂樓加蓋": "否",
        "產權登記": "無",
        "設備": ["熱水器", "洗衣機", "電視", "冰箱", "冷氣"],
        "家具": ["書桌", "椅子", "衣櫃", "雙人床"]
    }
}
    insert_good_info_to_rds("https://rent.housefun.com.tw/rent/house/1831664/", test_data["https://rent.housefun.com.tw/rent/house/1831664/"])
    '''
    good_infos = load_from_json(good_json_file_path)
    for good_info_url, content in good_infos.items():

        if good_info_url in all_h_url:
            print("Already in DB. Skip.")
            break

        insert_good_info_to_rds(good_info_url, content)
    '''

if __name__ == "__main__":
    main()