import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import KDTree
from sklearn.decomposition import PCA
from user_data_process import transform_one_use, transform_all_user
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


def get_value_from_dict(transform_all_user_data_dict):
    return list(transform_all_user_data_dict.values())


def match_ten_user(id_list, transform_select_user_data, cur_user_data):
    transform_select_user_data = np.array(transform_select_user_data)
    kdtree = KDTree(transform_select_user_data)
    distances, indices = kdtree.query(cur_user_data, k=10)

    # Print the indices of the nearest neighbors
    logger.info(f"Indices of nearest neighbors:")
    logger.info(f"{indices}")

    # Optionally, you can retrieve the actual data points corresponding to the indices
    nearest_neighbors = id_list[indices[0]]

    logger.info(f"Nearest neighbors:")
    logger.info(f"{nearest_neighbors}")
