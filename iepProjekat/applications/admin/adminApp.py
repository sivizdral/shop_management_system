from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import *
from sqlalchemy import func
from adminDecorator import isAdmin
from flask_jwt_extended import JWTManager, verify_jwt_in_request, get_jwt
import json

application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)


@application.route("/productStatistics", methods=["GET"])
@isAdmin(role="admin")
def getProductStatistics():
    products = Product.query.all()
    statistics = []

    for product in products:

        sold = 0
        waiting = 0

        ordered = OrderedProducts.query.filter(OrderedProducts.ProductId == product.id)

        for order in ordered:
            sold += order.requestedItems
            waiting += (order.requestedItems - order.receivedItems)

        object = {
            "name": product.name,
            "sold": sold,
            "waiting": waiting
        }

        if sold + waiting != 0:
            statistics.append(object)

    return Response(json.dumps({"statistics": statistics}), status=200)

@application.route("/categoryStatistics", methods=["GET"])
@isAdmin(role="admin")
def getCategoryStatistics():
    statistics = []

    categories = Category.query.outerjoin(ProductCategory).outerjoin(Product).outerjoin(OrderedProducts)
    categories = categories.group_by(Category.id).order_by(func.sum(OrderedProducts.requestedItems).desc()).order_by(Category.name)

    for category in categories:
        statistics.append(category.name)

    return Response(json.dumps({"statistics": statistics}), status=200)


if __name__ == "__main__":
    db.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5004)