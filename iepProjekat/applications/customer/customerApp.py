from flask import Flask, request, Response, jsonify
from applications.configuration import Configuration
from applications.models import *
from customerDecorator import isCustomer
from flask_jwt_extended import JWTManager
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
        else:
            category = str(item[1])

    if name == '' and category == '':
        cats = Category.query.all()
        for cat in cats:
            categories.append(cat.name)

        prods = Product.query.all()
        for prod in prods:
            pcs = []
            procats = ProductCategory.query.filter(ProductId=prod.id)
            for procat in procats:
                catname = Category.query.filter(id=procat.CategoryId).first().name
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
        cats = Category.query.filter(Category.name.contains(category))
        for cat in cats:
            categories.append(cat.name)

        prods = Product.query.all()
        for prod in prods:
            pcs = []
            procats = ProductCategory.query.filter(ProductId=prod.id)
            escape = False
            for procat in procats:
                catname = Category.query.filter(id=procat.CategoryId).first().name
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
        prods = Product.query.filter(Product.name.contains(name))
        for prod in prods:
            pcs = []
            procats = ProductCategory.query.filter(ProductId=prod.id)
            for procat in procats:
                catname = Category.query.filter(id=procat.CategoryId).first().name
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
            procats = ProductCategory.query.filter(CategoryId=cat.id)
            if len(procats) == 0:
                continue

            found = False
            for procat in procats:
                product = Product.query.filter(id=procat.ProductId)
                if (product.name.contains(name)):
                    found = True
                    break
            if found == True:
                categories.append(cat.name)

        prods = Product.query.filter(Product.name.contains(name))
        for prod in prods:
            pcs = []
            procats = ProductCategory.query.filter(ProductId=prod.id)
            if len(procats) == 0:
                continue

            found = False
            for procat in procats:
                cat = Category.query.filter(id=procat.CategoryId)
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


if __name__ == "__main__":
    db.init_app(application)
    application.run(debug=True, port=5003)