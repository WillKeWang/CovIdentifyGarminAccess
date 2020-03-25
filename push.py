from flask import Flask, jsonify
from flask_restful import reqparse, abort, Api, Resource
from pathlib import Path
from pymongo import MongoClient
import json
import urllib
import sys

app = Flask(__name__)
api = Api(app)

all_keys = []
parser = reqparse.RequestParser()
parser.add_argument('key')
parser.add_argument('summary_type')
parser.add_argument('file_name')

summary_list = ['dailies',
                'epochs',
                'thirdPartyDailies',
                'activities',
                'manuallyUpdatedActivities',
                'activityDetails',
                'sleeps',
                'bodyComps',
                'stressDetails',
                'userMetrics',
                'moveiq',
                'pulseOx']

user = password = urllib.parse.quote_plus('')
password = urllib.parse.quote_plus('')
ip = ""
port = ""
uri = f'mongodb://{user}:{password}@{ip}:{port}/?authSource=admin&authMechanism=SCRAM-SHA-256'
client = MongoClient(uri)
db = client["HealthDemo"]

keys = Path("Keys/")
key_path = keys / 'KeyList'
with open(key_path) as index_file:
    for line in index_file:
        all_keys.append(line.rstrip("\n\r"))


def error_check(key, summary_type, request_type):
    existing_keys = db.list_collection_names()
    existing_summary = db[key].find_one({"summary_type": summary_type})
    if key not in all_keys and request_type != "post":
        abort(400, message="This user is not registered.")
    if key not in existing_keys and request_type != "post":
        abort(400, message=f"No data available for user {key}")
    if summary_type not in summary_list:
        abort(400, message="Invalid data type.")
    if not existing_summary and request_type != "post":
        abort(400, message=f"No {summary_type} data available for user {key}")
    if summary_type == "" and (request_type == "post" or request_type == "put"):
        abort(400, message=f"A summary type needs to be provided for {request_type.capitalize()}")
    if existing_summary and request_type == "post":  # Do not want to overwrite data
        abort(400, message=f"{summary_type.capitalize()} data already exists for user {key}")


class HealthData(Resource):
    def get(self):
        args = parser.parse_args()
        key = args["key"]
        summary_type = args["summary_type"]
        error_check(key, summary_type, "get")

        if summary_type == "":
            return db[key].find_one()["Data"], 200

        else:
            summary_query = {"summary_type": summary_type}
            return db[key].find_one(summary_query)["Data"], 200

    def post(self):
        args = parser.parse_args()
        key = args["key"]
        summary_type = args["summary_type"]
        file_name = args["file_name"]
        error_check(key, summary_type, "post")

        with open(file_name) as json_of_a_bitch:
            new_data = {"summary_type": summary_type,
                        "Data": json.load(json_of_a_bitch)}
        db[key].insert_one(new_data)
        ret_json = {
            "Status": 200,
            "Message": f"{summary_type.capitalize()} data has been stored"
        }
        return jsonify(ret_json)

    def put(self):
        args = parser.parse_args()
        key = args["key"]
        summary_type = args["summary_type"]
        file_name = args["file_name"]
        error_check(key, summary_type, "put")

        with open(file_name) as json_of_a_bitch:
            new_data = {"Data": json.load(json_of_a_bitch)}

        data_list = list(new_data.values())[0]
        summary_query = {"summary_type": summary_type}
        db[key].update_one(summary_query,
                           {"$addToSet": {"Data": {"$each": data_list}}})

        ret_json = {
            "Status": 200,
            "Message": f"{summary_type.capitalize()} data has been updated"
        }
        return jsonify(ret_json)

    def delete(self):
        args = parser.parse_args()
        key = args["key"]
        summary_type = args["summary_type"]
        error_check(key, summary_type, "delete")

        if summary_type == "":
            db[key].delete_many({})

            ret_json = {
                "Status": 200,
                "Message": f"All data deleted for user {key}"
            }
            return jsonify(ret_json)

        else:
            summary_query = {"summary_type": summary_type}
            db[key].delete_one(summary_query)

            ret_json = {
                "Status": 200,
                "Message": f"{summary_type.capitalize()} data has been deleted"
            }
            return jsonify(ret_json)


class Hello(Resource):
    def get(self):
        return "Hello"


api.add_resource(Hello, "/")
api.add_resource(HealthData, '/health')  # Currently runs on local server, port 5000

if __name__ == "__main__":
    app.run(debug=True)
