import json
from faker import Faker
import random
import numpy as np
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics.pairwise import cosine_similarity
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


# Create a new collection
db = client['personal_project']


one_hot_encoding_cooking = {"seldoms": [
    1, 0, 0], "sometimes": [0, 1, 0], "always": [0, 0, 1], "None": [-1, -1, -1]}
one_hot_encoding_wake_time = {"before_6": [
    1, 0, 0], "6_to_9": [0, 1, 0], "after_9": [0, 0, 1], "None": [-1, -1, -1]}
one_hot_encoding_sleep_time = {"before_10": [
    1, 0, 0], "10_to_12": [0, 1, 0], "after_12": [0, 0, 1], "None": [-1, -1, -1]}
one_hot_encoding_gender = {"male": [1, 0, 0],
                           "female": [0, 1, 0], "non-binary": [0, 0, 1], "None": [-1, -1, -1]}
one_hot_encoding_career = {"student": [1, 0, 0, 0, 0, 0, 0, 0, 0], "worker": [0, 1, 0, 0, 0, 0, 0, 0, 0], "retiree": [0, 0, 1, 0, 0, 0, 0, 0, 0], "doctor": [0, 0, 0, 1, 0, 0, 0, 0, 0],
                           "engineer": [0, 0, 0, 0, 1, 0, 0, 0, 0], "teacher": [0, 0, 0, 0, 0, 1, 0, 0, 0], "designer": [0, 0, 0, 0, 0, 0, 1, 0, 0], "artist": [0, 0, 0, 0, 0, 0, 0, 1, 0], "other": [0, 0, 0, 0, 0, 0, 0, 0, 1], "None": [-1, -1, -1, -1, -1, -1, -1, -1, -1]}

qtf_partner = {"yes": 0, "no": 1, "None": -1}


qtf_zone = {"內湖區": 1, "中山區": 2, "松山區": 3, "士林區": 4, "南港區": 5, "萬華區": 6, "大同區": 7, "北投區": 8, "中正區": 9, "文山區": 10, "大安區": 11, "信義區": 12, "萬里區": 13, "金山區": 14, "板橋區": 15, "汐止區": 16, "深坑區": 17, "石碇區": 18, "瑞芳區": 19, "平溪區": 20,
            "雙溪區": 21, "貢寮區": 22, "新店區": 23, "坪林區": 24, "烏來區": 25, "永和區": 26, "中和區": 27, "土城區": 28, "三峽區": 29, "樹林區": 30, "鶯歌區": 31, "三重區": 32, "新莊區": 33, "泰山區": 34, "林口區": 35, "蘆洲區": 36, "五股區": 37, "八里區": 38, "淡水區": 39, "三芝區": 40, "石門區": 41}
qty_stay_with_landlord = {"yes": 0, "no": 1, "None": -1}
qtf_park = {"yes": 0, "no": 1, "None": -1}
qty_pet = {"yes": 0, "no": 1, "None": -1}
qtf_smoking = {"yes": 0, "no": 1, "None": -1}


qtf_equip = {"internet": 0, "cableTV": 1, "washingMachine": 2, "dryer": 3, "dryingMachine": 4, "waterDispenser": 5, "waterFilter": 6,
             "lcdTV": 7, "refrigerator": 8, "gasStove": 9, "microwave": 10, "oven": 11, "naturalGas": 12, "inductionCooker": 13, "electricFan": 14}
qtf_furniture = {"wardrobe": 0, "diningTable": 1, "diningChair": 2,
                 "cabinet": 3, "singleBed": 4, "doubleBed": 5, "desk": 6, "chair": 7, "sofa": 8}


def get_wake_time_category(time_str):
    if time_str == "None":
        return "None"
    # Convert time string to hours and minutes
    hours, minutes = map(int, time_str.split(':'))

    # Define the thresholds for each time category
    before_6_threshold = 6 * 60  # 6:00 AM in minutes
    after_8_threshold = 9 * 60  # 8:00 AM in minutes

    # Calculate the time in minutes since midnight
    time_in_minutes = hours * 60 + minutes

    # Check which category the time falls into
    if time_in_minutes < before_6_threshold:
        return "before_6"
    elif before_6_threshold <= time_in_minutes < after_8_threshold:
        return "6_to_9"
    else:
        return "after_9"


def get_sleep_time_category(time_str):
    if time_str == "None":
        return "None"
    # Convert time string to hours and minutes
    hours, minutes = map(int, time_str.split(':'))

    # Define the thresholds for each time category
    before_10_threshold = 10 * 60  # 10:00 AM in minutes
    after_12_threshold = 12 * 60  # 12:00 AM in minutes

    # Calculate the time in minutes since midnight
    time_in_minutes = hours * 60 + minutes

    # Check which category the time falls into
    if time_in_minutes < before_10_threshold:
        return "before_10"
    elif before_10_threshold <= time_in_minutes < after_12_threshold:
        return "10_to_12"
    else:
        return "after_12"


def transform_one_user(user):
    row = []
    gender_value = user.get("basic_info", {}).get("gender", "None")

    qtf_dict = {
        "user_id": user["user_id"],
        "username": user["username"],
        "gender": one_hot_encoding_gender.get(user.get("basic_info", {}).get("gender", "None"), [-1, -1, -1]),
        "identity": one_hot_encoding_career.get(user.get("basic_info", {}).get("identity", "None"), [-1, -1, -1, -1, -1, -1, -1, -1, -1]),
        "partner": qtf_partner.get(user.get("basic_info", {}).get("partner", "None"), -1),
        "introduction": user.get("basic_info", {}).get("introduction", ""),
        "price": int(user.get("house_preference", {}).get("price", 0)),
        "house_age": int(user.get("house_preference", {}).get("house_age", 0)),
        "stay_with_landlord": qty_stay_with_landlord.get(user.get("house_preference", {}).get("stay_with_landlord", "None"), -1),
        "park_nearby": qtf_park.get(user.get("house_preference", {}).get("park_nearby", "None"), -1),
        "sleep_time": one_hot_encoding_sleep_time.get(get_sleep_time_category(user.get("routine", {}).get("sleepTime", "None")), [-1, -1, -1]),
        "wake_time": one_hot_encoding_wake_time.get(get_wake_time_category(user.get("routine", {}).get("wakeUpTime", "None")), [-1, -1, -1]),
        "hygiene_tolerance": user.get("routine", {}).get("hygieneTolerance", -1),
        "noise_tolerance": user.get("routine", {}).get("noiseTolerance", -1),
        "cook_options": one_hot_encoding_cooking.get(user.get("routine", {}).get("cookOptions", "None"), [-1, -1, -1]),
        "pet_options": qty_pet.get(user.get("routine", {}).get("petOptions", "None"), -1),
        "smoke_options": qtf_smoking.get(user.get("routine", {}).get("smokeOptions", "None"), -1),
    }
    row.append(qtf_dict["price"])
    row.append(qtf_dict["partner"])
    row.append(qtf_dict["stay_with_landlord"])
    row.append(qtf_dict["house_age"])
    row.append(qtf_dict["noise_tolerance"])
    row.append(qtf_dict["park_nearby"])
    row.append(qtf_dict["pet_options"])
    row.append(qtf_dict["hygiene_tolerance"])
    row.append(qtf_dict["smoke_options"])

    row += qtf_dict["gender"] + qtf_dict["identity"] + \
        qtf_dict["sleep_time"] + qtf_dict["wake_time"] + \
        qtf_dict["cook_options"]

    user_dict = {"user_id": user["user_id"], "value": row}
    return row, user_dict


def transform_all_user(user_data):
    count = 0
    transform_all_user_data = []
    transform_all_user_data_dict = []

    for user in user_data:
        count += 1

        if count < 6:
            continue

        row, user_dict = transform_one_user(user)
        transform_all_user_data.append(row)
        transform_all_user_data_dict.append(user_dict)

    return transform_all_user_data_dict, transform_all_user_data


def match_user(id_list, transform_select_user_data, cur_user_data, match_num):
    transform_select_user_data = np.array(transform_select_user_data)
    kdtree = KDTree(transform_select_user_data)

    logger.info(f"Current user data : {cur_user_data}")

    distances, indices = kdtree.query([cur_user_data], k=match_num)

    # Optionally, you can retrieve the actual data points corresponding to the indices
    nearest_neighbors = [id_list[i] for i in indices[0]]

    return nearest_neighbors


def insert_transform_all_user_to_mongo(transform_all_user_collection, transform_all_user_data_dict):
    transform_all_user_collection.insert_many(transform_all_user_data_dict)


def get_value_from_user_dict(transform_all_user_data_dicts):
    id_list = []
    value_list = []
    for transform_all_user_data_dict in transform_all_user_data_dicts:
        id_list.append(transform_all_user_data_dict['user_id'])
        value_list.append(transform_all_user_data_dict['value'])
    return id_list, value_list
