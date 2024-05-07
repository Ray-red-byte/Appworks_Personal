import json
from faker import Faker
import random
import numpy as np
from sklearn.preprocessing import OneHotEncoder
from sklearn.neighbors import KDTree
from sklearn.decomposition import PCA
from dotenv import load_dotenv
import pymongo
import logging
import os

dotenv_path = '/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/.env'
load_dotenv(dotenv_path)

log_filename = os.getenv("APP_LOG_FILE_NAME")
log_file_path = os.getenv("APP_LOG_FILE_PATH")
logger = logging.getLogger(__name__)

# Mongo atlas
CONNECTION_STRING = os.getenv("MONGO_ATLAS_USER")
client = pymongo.MongoClient(CONNECTION_STRING)


'''
{"_id":{"$oid":"662253af2b1b2f13455e2ff8"},
 "id":{"$numberInt":"2"},
 "url":"https://rent.housefun.com.tw/rent/house/1831862/",
 "title":"近捷運三房美寓(房屋編號：035215)",
   "price":{"$numberDouble":"32800.0"},
 "address":"台北市北投區北投路一段\n租金行情",
 "type":"無電梯公寓",
 "usage":"None",
   "age":{"$numberInt":"43"},
 "face":"None",
 "env":"無",
   "size":{"$numberDouble":"28.0"},
 "short_stay":"12個月",
   "cook":true,
 "move_date":"2024年04月10日",
   "pet":"不可",
 "fee_contain":true,
   "gender":"男女皆可",
 "deposit":{"$numberInt":"-1"},
 "identy":"不限",
   "stay_landlord":true,
   "park":false,
 "equip":["熱水器","天然瓦斯","洗衣機","瓦斯爐","冰箱","冷氣"],
 "furniture":["衣櫃"],
 "floor":"3 / 4 樓",
 "corner":true,
 "center":false,
 "top_add":false,
 "img_url":"https://pic.hfcdn.com/res/DrawImage/ShowPic/400/300/HFRENT05/1831862/1?t=0921",
 "layout":"3房(室)2廳1衛",
 "updated_at":{"$date":{"$numberLong":"1713554479727"}}}
'''

# Create a new collection
db = client['personal_project']


def one_hot_gender(gender):
    if ("男" in gender and "女" in gender) or ("不限" in gender):
        return [1, 0, 0]
    elif "男" in gender and "女" not in gender:
        return [0, 1, 0]
    elif "女" in gender and "男" not in gender:
        return [0, 0, 1]
    else:
        return [-1, -1, -1]


def transform_one_house(house):
    row = []
    qtf_pet = {"不可": 0, "可": 1, "None": -1}
    qtf_dict = {
        "house_id": house["id"],
        "housename": house["title"],
        "price": house["price"],
        "age": -1 if house["age"] == "None" else house["age"],
        "size": house.get("size", -1),
        "cook": 1 if house.get("cook") is True else 0 if house.get("cook") is not None else -1,
        "pet": qtf_pet.get(house.get("pet", "None"), -1),
        "stay_with_landlord": 1 if house.get("stay_landlord") is True else 0 if house.get("stay_landlord") is not None else -1,
        "park": 1 if house.get("park") is True else 0 if house.get("park") is not None else -1,
        "gender": one_hot_gender(house["gender"])
    }
    row.append(qtf_dict["price"])
    row.append(qtf_dict["age"])
    row.append(qtf_dict["size"])
    row.append(qtf_dict["cook"])
    row.append(qtf_dict["pet"])
    row.append(qtf_dict["stay_with_landlord"])
    row.append(qtf_dict["park"])
    row += qtf_dict["gender"]

    house_dict = {"house_id": house["id"], "value": row}
    return row, house_dict


def transform_all_house(house_data):
    count = 0
    transform_all_house_data = []
    transform_all_house_data_dict = []

    for house in house_data:

        row, house_dict = transform_one_house(house)
        transform_all_house_data.append(row)
        transform_all_house_data_dict.append(house_dict)

    return transform_all_house_data_dict, transform_all_house_data


def match_house(id_list, transform_select_house_data, cur_house_data, match_num):
    transform_select_house_data = np.array(transform_select_house_data)
    kdtree = KDTree(transform_select_house_data)
    logger.info(f"Match house : {cur_house_data}")
    distances, indices = kdtree.query([cur_house_data], k=match_num)

    # Optionally, you can retrieve the actual data points corresponding to the indices
    nearest_neighbors = [id_list[i] for i in indices[0]]

    return nearest_neighbors


def insert_transform_all_house_to_mongo(transform_all_user_collection, transform_all_user_data_dict):
    transform_all_user_collection.insert_many(transform_all_user_data_dict)


def get_value_from_house_dict(transform_all_house_data_dicts):
    id_list = []
    value_list = []
    for transform_all_hosue_data_dict in transform_all_house_data_dicts:
        id_list.append(transform_all_hosue_data_dict['house_id'])
        value_list.append(transform_all_hosue_data_dict['value'])
    return id_list, value_list
