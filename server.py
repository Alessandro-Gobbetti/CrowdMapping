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

IP = "0.0.0.0"
PORT = 9999
MONGO_IP = "0.0.0.0"
MONGO_PORT = 27017

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

# TODO: remove this, just for testing purposes
# clear the collections
collection_stats.delete_many({})
collection_data.delete_many({})


# Example of received content:
# {"image": "base64_encoded_image",
#  "gps": "latitude,longitude",
#  "noise": "value",
#  "date": "date",
#  "id": "device_id"}


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

    results = model.predict(image)
    a = results[0].boxes.data
    px = pd.DataFrame(a).astype("float")
    # add class names to the dataframe
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


def add_new_data_to_db(people, vehicles, gps, noise, date, device_id):
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
    new_data = {
        "people": people,
        "vehicles": vehicles,
        "gps": gps,
        "noise": noise,
        "date": date,
        "device_id": device_id
    }
    collection_data.insert_one(new_data)

    update_stats(people, vehicles, gps, noise, date)


def approximate_gps(gps, precision=4):
    """
    Approximates a given GPS coordinate to the nearest grid points based on the specified precision.
    Args:
        gps (str): A string representing the GPS coordinates in the format "latitude,longitude".
        precision (int, optional): The precision for rounding the coordinates. Default is 4.
    Returns:
        list of tuples: A list of four tuples, each containing the latitude, longitude, and weight of the 
                        approximated grid points. The weights are computed using bilinear interpolation.
    """
    lat, lon = gps.split(",")
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

    return [(bottom_left[0], bottom_left[1], weights[0]),
            (bottom_right[0], bottom_right[1], weights[1]),
            (top_left[0], top_left[1], weights[2]),
            (top_right[0], top_right[1], weights[3])]


def update_stats(people, vehicles, gps, noise, date):
    """
    Updates the statistics collection in the database with the given data based on the GPS coordinates.
    The statistics are rolling mean values of the number of people, vehicles, and noise levels in a given area.
    The stats are updated based on the weights computed using bilinear interpolation.
    Old data is 
    """
    location = approximate_gps(gps)

    for loc in location:
        lat, lon, weight = loc
        # find the document with the given location
        doc = collection_stats.find_one({"gps": f"{lat},{lon}"})
        if doc is None:
            # create a new document
            new_doc = {
                "gps": f"{lat},{lon}",
                "people": people * weight,
                "vehicles": vehicles * weight,
                "noise": noise * weight,
                "date": date,
                "weight": weight
            }
            collection_stats.insert_one(new_doc)

        else:
            # update the document the rolling mean
            new_people = (doc["people"] * doc["weight"] +
                          people * weight) / (doc["weight"] + weight)
            new_vehicles = (doc["vehicles"] * doc["weight"] +
                            vehicles * weight) / (doc["weight"] + weight)
            new_noise = (doc["noise"] * doc["weight"] +
                         noise * weight) / (doc["weight"] + weight)

            collection_stats.update_one({"gps": f"{lat},{lon}"},
                                        {"$set": {"people": new_people,
                                                  "vehicles": new_vehicles,
                                                  "noise": new_noise,
                                                  "weight": doc["weight"] + weight}}
                                        )


def get_stats(gps):
    """
    Get the statistics for a given GPS coordinate.

    Args:
        gps (str): The GPS coordinates in the format "latitude,longitude".

    Returns:
        dict: A dictionary containing the statistics for the given GPS coordinates.
    """

    gps_approx = approximate_gps(gps)
    stats = []
    for loc in gps_approx:
        lat, lon, _ = loc
        doc = collection_stats.find_one({"gps": f"{lat},{lon}"})
        if doc:
            stats.append(doc)

    print(sum([loc[2] for loc in gps_approx]))
    result = {}
    # compute the weighted average of the statistics
    for stat, weight in zip(stats, [loc[2] for loc in gps_approx]):
        for key in ["people", "vehicles", "noise"]:
            if key in result:
                result[key] += stat[key] / stat["weight"] * weight
            else:
                result[key] = stat[key] / stat["weight"] * weight

    return result


def handle_client(client_socket):
    """
    Handles the client connection, receives data, processes the image, counts objects, and stores data in the database.

    Args:
        client_socket (socket.socket): The socket object for the client connection.

    The function performs the following steps:
        1. Receives data from the client in chunks of 1 MB until all data is received.
        2. Parses the received data as a JSON object.
        3. Decodes the base64-encoded image from the JSON object.
        4. Converts the image to a NumPy array and reshapes it to the expected dimensions.
        5. Counts the number of people and vehicles in the image.
        6. Stores the counted objects and additional data in a MongoDB database.
    """
    buffer_size = 1024 * 1024  # 1 MB buffer size
    data = b""

    while True:
        part = client_socket.recv(buffer_size)
        data += part
        if len(part) < buffer_size:
            break
        print("Receiving data...")

    print(f"Received {len(data)} bytes")
    client_socket.close()

    # parse request
    request = json.loads(data.decode())
    image = request.get("image")
    image = base64.b64decode(image)

    image = np.frombuffer(image, dtype=np.uint8)
    image = image.reshape((240, 320))

    # image to rgb for yolo
    image = np.stack((image,) * 3, axis=-1)

    # save image with matplotlib
    # plt.imshow(image, cmap='gray')
    # plt.savefig("received_image.png")

    # count objects
    people, vehicles = count_objects(image)
    print(f"Detected {people} people and {vehicles} vehicles")

    # push data to mongo database
    # FIXME: add the rest of the data
    gps = request.get("gps") or "0,0"
    noise = int(request.get("noise") or "0")
    date = request.get("date") or "0"
    device_id = request.get("id") or "0"

    add_new_data_to_db(people, vehicles, gps, noise, date, device_id)

    # TODO: remove this, just for testing purposes
    print_all_db()
    print("------------------"*3)
    print(get_stats(gps))


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((IP, PORT))
    server.listen(5)

    server_ip = socket.gethostbyname(socket.gethostname())
    print(f"Server started at {server_ip}:{PORT}")

    while True:
        client_socket, addr = server.accept()
        print(f"Accepted connection from {addr}")

        client_handler = threading.Thread(
            target=handle_client, args=(client_socket,))
        client_handler.start()


if __name__ == "__main__":
    main()
