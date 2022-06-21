from flask import Flask, request, Response, jsonify
from applications.configuration import Configuration
from applications.models import *
from redis import Redis
from warehousemanDecorator import isWarehouseman
from flask_jwt_extended import JWTManager
import json, csv

application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)


@application.route("/update", methods=["POST"])
@isWarehouseman(role="warehouseman")
def updateProducts():
    fileName = request.json.get("file", "")

    if len(fileName) == 0:
        return Response(json.dumps({"message":"Field file missing."}), status=400)

    csv_file = open(fileName)
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0

    redis = Redis(host=Configuration.REDIS_HOST)

    for row in csv_reader:
        if len(row) != 4:
            msg = "Incorrect number of values on line " + str(line_count) + "."
            return Response(json.dumps({"message":msg}), status=400)

        if not row[2].isdigit() or int(row[2]) == 0:
            msg = "Incorrect quantity on line " + str(line_count) + "."
            return Response(json.dumps({"message":msg}), status=400)

        try:
            price = float(row[3])
        except ValueError:
            msg = "Incorrect price on line " + str(line_count) + "."
            return Response(json.dumps({"message":msg}), status=400)

        if price == 0:
            msg = "Incorrect price on line " + str(line_count) + "."
            return Response(json.dumps({"message": msg}), status=400)

        line_count += 1
        sendMessage = ','.join(row)
        redis.publish(channel="warehouseUpdates", message=sendMessage)

    return Response(status=200)


if __name__ == "__main__":
    db.init_app(application)
    application.run(debug=True, port=5001)
