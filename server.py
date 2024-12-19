import datetime
from flask import Flask, jsonify, request, Blueprint
from flask_cors import CORS
import base64
import matplotlib.pyplot as plt
import socket
import threading
from ultralytics import YOLO
import json
import pandas as pd
import numpy as np
import pymongo
import math
import os

IP = "0.0.0.0"
PORT = 9999
MONGO_IP = "0.0.0.0"
MONGO_PORT = 27017

GPS_PRECISION = 0.001

# YOLO model to detect objects in images
print("Loading model...")
model = YOLO('yolov8s.pt')
file = open('coco.names', 'r')
data = file.read()
class_list = data.split('\n')
file.close()


# MongoDB connection
client = pymongo.MongoClient(f"mongodb://{MONGO_IP}:{MONGO_PORT}/")
db = client["CrowdMap"]
collection_stats = db["Stats"]
collection_data = db["Data"]


def count_objects(image):
    """
    Count the number of people and vehicles in an image.

    Args:
        image: The input image to be processed.

    Returns:
        A tuple containing:
            - The number of people detected in the image.
            - The number of vehicles detected in the image.
    """
    vehicle_types = ['car', 'motorcycle', 'bus', 'truck']

    # yolo on grayscale image

    results = model.predict(image)
    a = results[0].boxes.data
    px = pd.DataFrame(a).astype("float")
    # add class names to the dataframe
    # i added a try, except for when detection doesn't find anything
    # (i assume that's the problem, giving an empty px that has no px[5] column)
    try:
        px['class'] = px[5].map(lambda x: class_list[int(x)])

        people = []
        vehicles = []

        for index, row in px.iterrows():
            x1 = int(row[0])
            y1 = int(row[1])
            x2 = int(row[2])
            y2 = int(row[3])
            d = int(row[5])

            c = class_list[d]

            if 'person' in c:
                people.append([x1, y1, x2, y2])
            elif c in vehicle_types:
                vehicles.append([x1, y1, x2, y2])

        return len(people), len(vehicles)
    except:
        return 0, 0


def print_all_db():
    """
    Prints all documents from two MongoDB collections: 'collection_data' and 'collection_stats'.
    """
    query = collection_data.find()
    print("------------------ Data:")
    for data in query:
        print(data)

    query = collection_stats.find()
    print("------------------ Statistics:")
    for stat in query:
        print(stat)


def populate_db():

    demo_data = [
        {
            "people": 210,
            "vehicles": 130,
            "gps_lat": 46.016800360890905,
            "gps_lon": 8.957521910617551,
            "noise": 160,
            "date": "2024-12-18 22:30:35",
            "device_id": "device_123"
        },
        {
            "people": 160,
            "vehicles": 100,
            "gps_lat": 46.00511056282624,
            "gps_lon": 8.952675611058293,
            "noise": 55,
            "date": "2024-12-18 23:30:35",
            "device_id": "device_456"
        },
        {
            "people": 90,
            "vehicles": 5,
            "gps_lat": 46.007423160698565,
            "gps_lon": 8.952180968730389,
            "noise": 120,
            "date": "2024-12-18 21:30:35",
            "device_id": "device_456"
        },
        {
            "people": 120,
            "vehicles": 60,
            "gps_lat": 46.00950219494022,
            "gps_lon": 8.952889071904426,
            "noise": 80,
            "date": "2024-12-18 20:30:35",
            "device_id": "device_456"
        }
    ]

    for data in demo_data:
        add_new_data_to_db(data["people"], data["vehicles"], data["gps_lat"],
                           data["gps_lon"], data["noise"], data["date"], data["device_id"])

    print("Populated the database with demo data.")
    print_all_db()


def add_new_data_to_db(people, vehicles, gps_lat, gps_lon, noise, date, device_id):
    """
    Adds new data to the database and updates statistics.

    Args:
        people (int): The number of people detected.
        vehicles (int): The number of vehicles detected.
        gps (dict): The GPS coordinates where the data was collected.
        noise (float): The noise level detected.
        date (str): The date when the data was collected.
        device_id (str): The ID of the device that collected the data.
    Returns:
        None
    """

    # convert date to datetime
    date = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

    new_data = {
        "people": people,
        "vehicles": vehicles,
        "gps_lat": gps_lat,
        "gps_lon": gps_lon,
        "noise": noise,
        "date": date,
        "device_id": device_id
    }
    collection_data.insert_one(new_data)

    update_stats(people, vehicles, gps_lat, gps_lon, noise, date)


def approximate_gps(gps_lat, gps_lon, precision=1000):
    """
    Approximates a given GPS coordinate to the nearest grid points based on the specified precision.
    Args:
        gps (str): A string representing the GPS coordinates in the format "latitude,longitude".
        precision (int, optional): The precision for rounding the coordinates. Default is 4.
    Returns:
        list of tuples: A list of four tuples, each containing the latitude, longitude, and weight of the
                        approximated grid points. The weights are computed using bilinear interpolation.
    """
    lat, lon = gps_lat, gps_lon
    lat = float(lat)
    lon = float(lon)

    # round down to the nearest precision
    bottom_left = (math.floor(lat * precision) / precision,
                   math.floor(lon * precision) / precision)
    bottom_right = (math.floor(lat * precision) / precision,
                    math.ceil(lon * precision) / precision)
    top_left = (math.ceil(lat * precision) / precision,
                math.floor(lon * precision) / precision)
    top_right = (math.ceil(lat * precision) / precision,
                 math.ceil(lon * precision) / precision)

    # compute the weights Bi linear Interpolation
    weights = []
    for location in [bottom_left, bottom_right, top_left, top_right]:
        clat, clon = location
        weight = (1 - abs(clat - lat)) * (1 - abs(clon - lon))
        weights.append(weight)
    # normalize the weights
    weights = [weight / sum(weights) for weight in weights]

    res = [(bottom_left[0], bottom_left[1], weights[0]),
           (bottom_right[0], bottom_right[1], weights[1]),
           (top_left[0], top_left[1], weights[2]),
           (top_right[0], top_right[1], weights[3])]

    # sum the weights if the coordinates are the same
    combined = {}
    for x, y, z in res:
        if (x, y) in combined:
            combined[(x, y)] += z
        else:
            combined[(x, y)] = z

    # Convert the dictionary back to a list
    res = [(x, y, z) for (x, y), z in combined.items()]

    return res


def update_stats(people, vehicles, gps_lat, gps_lon, noise, date):
    """
    Updates the statistics collection in the database with the given data based on the GPS coordinates.
    The statistics stored in the database are the sum of the people, vehicles, and noise weighted by the distance to the center of the grid point.
    The weights are computed using bilinear interpolation based on the distance to the four nearest grid points (see approximate_gps function).
    """
    location = approximate_gps(gps_lat, gps_lon)
    print("Location", location)

    for loc in location:
        lat, lon, weight = loc
        # find the document with the given location
        doc = collection_stats.find_one({"gps_lat": lat, "gps_lon": lon})
        if doc is None:
            # create a new document
            new_doc = {
                "gps_lat": lat,
                "gps_lon": lon,
                "people": people * weight,
                "vehicles": vehicles * weight,
                "noise": noise * weight,
                "date": date,
                "weight": weight
            }
            collection_stats.insert_one(new_doc)

        else:
            # update the document the rolling mean
            new_people = doc["people"] + people * weight
            new_vehicles = doc["vehicles"] + vehicles * weight
            new_noise = doc["noise"] + noise * weight

            collection_stats.update_one({"gps_lat": lat, "gps_lon": lon},
                                        {"$set": {"people": new_people,
                                                  "vehicles": new_vehicles,
                                                  "noise": new_noise,
                                                  "weight": doc["weight"] + weight}}
                                        )


def get_stats(gps_lat, gps_lon):
    """
    Get the statistics for a given GPS coordinate.
    This function queries the statistics collection in the database for the given GPS coordinates and returns the statistics.
    A separate database is used to precompute statistics for each grid point based on the data collected.
    Statistics are updated when new data is added to the main database (see update_stats function).

    Args:
        gps (str): The GPS coordinates in the format "latitude,longitude".

    Returns:
        dict: A dictionary containing the statistics for the given GPS coordinates.
    """

    gps_approx = approximate_gps(gps_lat, gps_lon)
    stats = []
    for loc in gps_approx:
        lat, lon, _ = loc
        doc = collection_stats.find_one({"gps_lat": lat, "gps_lon": lon})
        if doc:
            stats.append(doc)

    print("SUM", sum([loc[2] for loc in gps_approx]))
    result = {}

    # normalize the weights
    stats_weight_sum = sum(stat["weight"] for stat in stats)
    # compute the weighted average of the statistics
    for stat, weight in zip(stats, [loc[2] for loc in gps_approx]):
        for key in ["people", "vehicles", "noise"]:

            print("STAT", weight, stat[key], stat["weight"])
            if key in result:
                result[key] += stat[key] / stat["weight"] * weight
            else:
                result[key] = stat[key] / stat["weight"] * weight

    return result


def get_avg_stats(gps_lat, gps_lon):
    """
    Get the average statistics for a given GPS coordinate and its neighbors.
    This function queries the database for the neighbors of the given GPS coordinate and computes the weighted average of the statistics based on the distance to the center.
    This is less efficient then the get_stats function as it requires mulitple queries to the database and more computation.

    Args:
        gps_lat (float): The latitude of the GPS coordinates.
        gps_lon (float): The longitude of the GPS coordinates.
        neigh (list): A list of dictionaries containing the statistics for the neighbors.

    Returns:
        dict: the weighted average of the statistics for the given GPS coordinate and its neighbors based on the distance.
    """
    result = {}
    neigh = collection_data.find(
        {"gps_lat": {"$gte": gps_lat - GPS_PRECISION, "$lte": gps_lat + GPS_PRECISION},
         "gps_lon": {"$gte": gps_lon - GPS_PRECISION, "$lte": gps_lon + GPS_PRECISION}})
    neigh = list(neigh)
    # average the stats based on the distance to the center
    sigma = 0.1
    total_weight = 0

    for n in neigh:
        distance = math.sqrt((n["gps_lat"] - gps_lat) **
                             2 + (n["gps_lon"] - gps_lon) ** 2)
        weight = math.exp(-distance**2 / (2 * sigma**2))

        for key in ["people", "vehicles", "noise"]:
            if key in result:
                result[key] += n[key] * weight
            else:
                result[key] = n[key] * weight

        total_weight += weight

    for key in ["people", "vehicles", "noise"]:
        result[key] /= total_weight

    return result


# TODO: remove this, just for testing purposes
# clear the collections
collection_stats.delete_many({})
collection_data.delete_many({})
populate_db()

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 1600 * 1024 * 1024


def main():
    app.run(host='0.0.0.0', port=9999, threaded=True, debug=True)


@app.route('/get', methods=['GET'])
def get_statistics():
    """
    Get the data and statistics on the history of the neighborhood of each entry in the database for a given date range.
    Only most recent data from sanme device when in the same location is considered.
    """

    date_range = request.args.get("date_range")
    print("DATE_RANGE", date_range)
    if date_range is not None:
        date_range = date_range.split(",")
        date_range = [datetime.datetime.strptime(date_range[0], "%Y-%m-%d %H:%M:%S"),
                      datetime.datetime.strptime(date_range[1], "%Y-%m-%d %H:%M:%S")]
    else:
        date_range = [datetime.datetime.now() - datetime.timedelta(hours=2),
                      datetime.datetime.now() + datetime.timedelta(weeks=52)]

    pipeline = [
        {"$match": {"date": {"$gte": date_range[0], "$lte": date_range[1]}}},
        {"$sort": {"date": -1}},
        {"$group": {
            "_id": {
                "device_id": "$device_id",
                "gps_lat": {"$round": ["$gps_lat", -int(math.log10(GPS_PRECISION))]},
                "gps_lon": {"$round": ["$gps_lon", -int(math.log10(GPS_PRECISION))]}
            },
            "most_recent": {"$first": "$$ROOT"}
        }},
        {"$replaceRoot": {"newRoot": "$most_recent"}}
    ]
    query = collection_data.aggregate(pipeline)

    query_list = list(query)
    # remove the id
    for q in query_list:
        del q["_id"]
        # range query gps with precision
        stats = get_stats(q["gps_lat"], q["gps_lon"])
        q["stats_people"] = stats["people"]
        q["stats_vehicles"] = stats["vehicles"]
        q["stats_noise"] = stats["noise"]

    print("QUERY", query_list)
    # reply with the statistics
    return jsonify({"status": "success", "data": query_list}), 200


@app.route('/upload', methods=['POST'])
def upload_data():

    data = request.get_data()
    # print(len(data))
    # parse request: split data into image and metadata
    # there's only one println
    parsed_data = data.split(b'\r\n')

    if len(parsed_data) != 2:
        return jsonify({"status": "error", "message": "Missing data"}), 400

    json_data, image = parsed_data
    json_data = json_data.decode()  # convert bytes to string
    # handle the case when the json data is not valid
    try:
        json_data = json.loads(json_data)

    except json.JSONDecodeError:
        return jsonify({"status": "error", "message": "Invalid JSON data"}), 400

    # read the raw the image data
    try:
        image_array = np.frombuffer(image, dtype=np.uint8).reshape((240, 320))
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid image data"}), 400

    # save the image to a file
    # image_filename = os.path.join("images", "last_image.png")
    # plt.imsave(image_filename, image_array, cmap='gray')

    image = np.stack((image_array,) * 3, axis=-1)
    people, vehicles = count_objects(image)

    # push data to mongo database
    gps_lat = float(json_data.get("gps_lat")) or 0.0
    gps_lon = float(json_data.get("gps_lon")) or 0.0
    noise = float(json_data.get("noise") or 0)
    date = json_data.get("date") or datetime.datetime.now().isoformat()

    # todo: parse date
    # doesn't work if you reassign the variable date from str to datetime
    date_object = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
    print(date_object.isoformat()) # like 2023-10-01T12:00:00
    device_id = json_data.get("id") or "0"

    # replace `date` with `date_object.isoformat()` if you want a string, or just `date_object` if you want a datetime object
    add_new_data_to_db(people, vehicles, gps_lat,
                       gps_lon, noise, date, device_id)

    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400

    return jsonify({"status": "success"}), 200


if __name__ == "__main__":
    main()
