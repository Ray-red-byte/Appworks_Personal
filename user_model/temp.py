temp = "3 / 4 樓"


def get_floor(floor_str):
    if floor_str == "None":
        return -1
    return int(floor_str.split('/')[0].strip())


print(get_floor(temp))
