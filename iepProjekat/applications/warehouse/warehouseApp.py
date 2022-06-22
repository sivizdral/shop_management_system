from flask import Flask, request, Response, jsonify
from werkzeug.utils import secure_filename

from configuration import Configuration
from models import *
from redis import Redis
from warehousemanDecorator import isWarehouseman
from flask_jwt_extended import JWTManager
import json, csv, io

application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)


@application.route("/update", methods=["POST"])
@isWarehouseman(role="warehouseman")
def updateProducts():
    file = request.files.get('file', None)

    if not file:
        return Response(json.dumps({"message": "Field file is missing."}), status=400)

    file = file.stream.read().decode("utf-8")
    stream = io.StringIO(file)
    csv_reader = csv.reader(stream, delimiter=',')
    line_count = 0

    messages = []

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

        if price <= 0:
            msg = "Incorrect price on line " + str(line_count) + "."
            return Response(json.dumps({"message": msg}), status=400)

        line_count += 1
        sendMessage = ','.join(row)
        messages.append(sendMessage)

    for message in messages:
        redis.publish(channel="warehouseUpdates", message=message)

    return Response(status=200)


if __name__ == "__main__":
    db.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5001)
