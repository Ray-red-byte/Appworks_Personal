import json
import pymysql
from dotenv import load_dotenv
import os
import boto3
from botocore.exceptions import NoCredentialsError


# MySQL 
mysql_host = os.getenv("DB_HOST")
mysql_user = os.getenv("DB_USER")
mysql_pwd = os.getenv("DB_PASSWORD")
mysql_db = os.getenv("DB_DATABASE")


# S3 setting
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
aws_secret_access_key = os.getenv("S3_SECRET_ACCESS_KEY")
aws_access_key_id = os.getenv("S3_ACCESS_KEY")
aws_bucket = os.getenv("S3_BUCKET_NAME")
s3_good_info_path = 'personal_project/house_detail/good_details/rent_good_info.json'
s3_good_url_path = 'personal_project/urls/good_urls/rent_good_url.json'
local_good_info_file = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/data/rent_good_info.json'
local_good_url_file = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/data/rent_good_url.json'


# connect to mysql
conn = pymysql.connect(
    host=mysql_host,
    user=mysql_user,
    password=mysql_pwd,
    database=mysql_db
)

cursor = conn.cursor()


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


def insert_good_info_to_rds(good_info, cursor):
    try:
        for info in good_info:
            # Assuming `good_info` is a list of dictionaries
            sql = """
                    INSERT INTO your_table_name (column1, column2, ...) 
                    VALUES (%s, %s, ...);
                  """
            # Execute the SQL query
            cursor.execute(sql, (info['column1'], info['column2'], ...))  # Replace column names accordingly
        # Commit the changes
        conn.commit()
        print("Data inserted successfully.")
    except Exception as e:
        # Rollback in case of any error
        conn.rollback()
        print("Error:", e)


def main():
    good_info = load_from_json(hap_json_file_path)
    print(good_info)

if __name__ == "__main__":
    main()