from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import *
from customerDecorator import isCustomer
from flask_jwt_extended import JWTManager, verify_jwt_in_request, get_jwt
import json

application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)


@application.route("/search", methods=["GET"])
@isCustomer(role="customer")
def searchProducts():
    items = request.args.items()
    name = ''
    category = ''
    products = []
    categories = []

    for item in items:
        if (str(item[0]) == "name"):
            name = str(item[1])
        elif (str(item[0]) == "category"):
            category = str(item[1])

    if name == '' and category == '':
        cats = Category.query.all()
        for cat in cats:
            categories.append(cat.name)

        prods = Product.query.all()
        for prod in prods:
            pcs = []
            procats = ProductCategory.query.filter(ProductCategory.ProductId == prod.id).all()
            for procat in procats:
                catname = Category.query.filter(Category.id == procat.CategoryId).first().name
                pcs.append(catname)

            object = {
                "categories" : pcs,
                "id": prod.id,
                "name": prod.name,
                "price": prod.price,
                "quantity": prod.availableQuantity
            }
            products.append(object)

        return Response(json.dumps({"categories": categories, "products": products}), status=200)

    elif name == '':
        cats = Category.query.filter(Category.name.contains(category)).all()
        for cat in cats:
            categories.append(cat.name)

        prods = Product.query.all()
        for prod in prods:
            pcs = []
            procats = ProductCategory.query.filter(ProductCategory.ProductId == prod.id).all()
            escape = False
            for procat in procats:
                catname = Category.query.filter(Category.id == procat.CategoryId).first().name
                if not catname in categories:
                    escape = True
                    break
                else:
                    pcs.append(catname)

            if escape == True:
                continue

            object = {
                "categories": pcs,
                "id": prod.id,
                "name": prod.name,
                "price": prod.price,
                "quantity": prod.availableQuantity
            }
            products.append(object)

        return Response(json.dumps({"categories": categories, "products": products}), status=200)

    elif category == '':
        prods = Product.query.filter(Product.name.contains(name)).all()
        for prod in prods:
            pcs = []
            procats = ProductCategory.query.filter(ProductCategory.ProductId == prod.id).all()
            for procat in procats:
                catname = Category.query.filter(Category.id == procat.CategoryId).first().name
                pcs.append(catname)
                if not catname in categories:
                    categories.append(catname)

            object = {
                "categories": pcs,
                "id": prod.id,
                "name": prod.name,
                "price": prod.price,
                "quantity": prod.availableQuantity
            }
            products.append(object)
        return Response(json.dumps({"categories": categories, "products": products}), status=200)

    else:
        cats = Category.query.filter(Category.name.contains(category))
        for cat in cats:
            procats = ProductCategory.query.filter(ProductCategory.CategoryId == cat.id).all()
            if len(procats) == 0:
                continue

            found = False
            for procat in procats:
                product = Product.query.filter(Product.id == procat.ProductId).all()
                if (product.name.contains(name)):
                    found = True
                    break
            if found == True:
                categories.append(cat.name)

        prods = Product.query.filter(Product.name.contains(name)).all()
        for prod in prods:
            pcs = []
            procats = ProductCategory.query.filter(ProductCategory.ProductId == prod.id).all()
            if len(procats) == 0:
                continue

            found = False
            for procat in procats:
                cat = Category.query.filter(Category.id == procat.CategoryId).all()
                pcs.append(cat.name)
                if cat.name.contains(category):
                    found = True

            if not found:
                continue

            object = {
                "categories": pcs,
                "id": prod.id,
                "name": prod.name,
                "price": prod.price,
                "quantity": prod.availableQuantity
            }
            products.append(object)

        return Response(json.dumps({"categories": categories, "products": products}), status=200)


@application.route("/order", methods=["POST"])
@isCustomer(role="customer")
def orderProducts():
    requests = request.json.get("requests", "")

    if len(requests) == 0:
        return Response(json.dumps({"message": "Field requests is missing."}), status=400)

    req_number = 0
    for req in requests:
        id = req.get("id", "")
        quantity = req.get("quantity", "")

        if id == "":
            msg = "Product id is missing for request number " + str(req_number) + "."
            return Response(json.dumps({"message": msg}), status=400)
        if quantity == "":
            msg = "Product quantity is missing for request number " + str(req_number) + "."
            return Response(json.dumps({"message": msg}), status=400)

        if (type(id) == str and not id.isdigit()) or int(id) <= 0:
            msg = "Invalid product id for request number " + str(req_number) + "."
            return Response(json.dumps({"message": msg}), status=400)

        if (type(quantity) == str and not quantity.isdigit()) or int(quantity) <= 0:
            msg = "Invalid product quantity for request number " + str(req_number) + "."
            return Response(json.dumps({"message": msg}), status=400)

        product = Product.query.filter(Product.id == int(id)).first()

        if not product:
            msg = "Invalid product for request number " + str(req_number) + "."
            return Response(json.dumps({"message": msg}), status=400)

        req_number += 1

    verify_jwt_in_request()
    claims = get_jwt()
    email = claims['email']
    order = Order(price=0, status="W", email=email)
    db.session.add(order)
    db.session.commit()
    fulfilled = True

    for req in requests:
        id = int(req["id"])
        quantity = int(req["quantity"])

        product = Product.query.filter(Product.id == id).first()
        price = product.price * quantity
        available = product.availableQuantity
        delivered = 0

        if available >= quantity:
            product.availableQuantity -= quantity
            delivered = quantity
            db.session.commit()
        else:
            product.availableQuantity = 0
            delivered = available
            db.session.commit()

        if delivered != quantity:
            fulfilled = False

        orderedProduct = OrderedProducts(OrderId=order.id, ProductId=product.id, requestedItems=quantity, receivedItems=delivered)
        db.session.add(orderedProduct)
        db.session.commit()

        order.price += price
        db.session.commit()

    if fulfilled:
        order.status = "F"
        db.session.commit()

    return Response(json.dumps({"id": order.id}), status=200)


@application.route("/status", methods=["GET"])
@isCustomer(role="customer")
def checkOrders():

    verify_jwt_in_request()
    claims = get_jwt()
    email = claims['email']
    orders = []

    myOrders = Order.query.filter(Order.email == email).all()

    for myOrder in myOrders:
        products = OrderedProducts.query.filter(OrderedProducts.OrderId == myOrder.id).all()
        p_list = []

        for product in products:
            prod = Product.query.filter(Product.id == product.ProductId).first()
            pcs = []
            procats = ProductCategory.query.filter(ProductCategory.ProductId == prod.id).all()

            for procat in procats:
                cat = Category.query.filter(Category.id == procat.CategoryId).first()
                pcs.append(cat.name)

            object = {
                "categories": pcs,
                "name": prod.name,
                "price": prod.price,
                "received": product.receivedItems,
                "requested": product.requestedItems
            }
            p_list.append(object)

        status = 'PENDING'
        if myOrder.status == "F":
            status = "COMPLETE"

        object = {
            "products": p_list,
            "price": myOrder.price,
            "status": status,
            "timestamp": str(myOrder.creationTime)
        }

        orders.append(object)

    return Response(json.dumps({"orders":orders}), status=200)



if __name__ == "__main__":
    db.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5003)