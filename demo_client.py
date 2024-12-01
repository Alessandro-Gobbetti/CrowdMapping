# create a client to connect to the server
#
import numpy as np
import socket
import json

SERVER_IP = "localhost"
SERVER_PORT = 9999


def main():
    # client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # client.connect((SERVER_IP, SERVER_PORT))
    # print("Connected to server")
    # send a request
    import base64
    image_path = "./image_0000.raw"

    with open(image_path, "rb") as image_file:
        raw_image = image_file.read()
        np_image = np.frombuffer(raw_image, dtype=np.uint8)
        print(f"Read image of size {len(np_image)}")
        np_image = np_image.reshape((240, 320))

        encoded_image = base64.b64encode(np_image).decode()

    data = {
        "image": encoded_image,
        "gps": "37.7749,-122.4194",  # Example GPS coordinates
        "noise": "50",  # Example noise value
        "date": "2023-10-01 12:00:00",  # Example date
        "id": "device_123"  # Example device ID
    }
    json_data = json.dumps(data)

    # Create a socket and connect to the server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, SERVER_PORT))

    # Send the JSON data
    client_socket.sendall(json_data.encode('utf-8'))

    # print message size
    print(f"Sent {len(json_data)} bytes")

    # Close the socket
    client_socket.close()

    # # image = open("./image_0000.raw", "rb").read()
    # image = base64.b64encode(image).decode()
    # request = {
    #     "image": image,
    # }
    # request = json.dumps(request)
    # client.sendall(request.encode('utf-8'))
    # print("Request sent")
    # client.close()

    # decode the request
    # request = json.loads(request)
    # image = request.get("image")
    # image = base64.b64decode(image)
    # print(f"Received image of size {len(image)}")
    # client.close()


if __name__ == "__main__":
    main()
