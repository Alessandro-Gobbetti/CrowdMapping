# CrowdMapping

## How to run

### Step 1: Install the required packages

Install mongodb, you can follow the instructions [here](https://www.mongodb.com/docs/manual/installation/). MongoDB Compass can be useful for visualizing the database, you can download it [here](https://www.mongodb.com/try/download/compass).

Install the necessary Python packages using the `requirements.txt` file:

```sh
conda create --name <env> --file requirements.txt
```

Activate the environment:

```sh
conda activate <env>
```

### Step 2: Set up MongoDB

Start the MongoDB server:

```sh
mongod --dbpath <path_to_your_mongo_db_directory>
```

Ensure MongoDB is running on `localhost` and port `27017`.

### Step 3: Run the server

Navigate to the `CrowdMapping` directory and run the `server.py` script:

```sh
cd CrowdMapping
python server.py
```

The server will start and listen for incoming connections on `localhost:9999`.
The model will be loaded and the database will be connected to.

### Step 4: Test with the demo client

Run the `demo_client.py` script to send a test request to the server:

```sh
python demo_client.py
```

This script will connect to the server and send a sample image (`image_0000.raw`) along with some metadata.
