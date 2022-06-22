import threading
import redis
from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import *

application = Flask(__name__)
application.config.from_object(Configuration)
db.init_app(application)

with application.app_context() as context:

    red = redis.StrictRedis(host=Configuration.REDIS_HOST, charset="utf-8", decode_responses=True)
    pubsub = red.pubsub()
    pubsub.subscribe("warehouseUpdates")

    while (True):
        for msg in pubsub.listen():
            msg = msg['data']
            if not type(msg) == str:
                continue
            row = msg.split(',')
            categories = row[0].split('|')
            name = row[1]
            quantity = int(row[2])
            price = float(row[3])
            product = Product.query.filter(Product.name == name).first()
            if not product:
                product = Product(name=name, availableQuantity=quantity, price=price)
                db.session.add(product)
                db.session.commit()

                for category in categories:
                    cat = Category.query.filter(Category.name == category).first()
                    if not cat:
                        cat = Category(name=category)
                        db.session.add(cat)
                        db.session.commit()

                        pro_cat = ProductCategory(ProductId=product.id, CategoryId=cat.id)
                        db.session.add(pro_cat)
                        db.session.commit()

                    else:
                        pro_cat = ProductCategory(ProductId=product.id, CategoryId=cat.id)
                        db.session.add(pro_cat)
                        db.session.commit()

            else:
                product_categories = ProductCategory.query.filter(ProductCategory.ProductId == product.id).all()

                pcs = []
                for pc in product_categories:
                    pcs.append(Category.query.filter(Category.id == pc.CategoryId).first().name)

                if set(categories) != set(pcs):
                    continue

                currentQuantity = product.availableQuantity
                currentPrice = product.price

                newPrice = (currentQuantity * currentPrice + quantity * price) / (currentQuantity + quantity)

                product.price = newPrice
                product.availableQuantity += quantity
                db.session.commit()

            orders = Order.query.filter(Order.status == "W").join(OrderedProducts).join(Product).filter(Product.name == product.name).group_by(Order.id).order_by(Order.creationTime).all()

            for order in orders:
                orderedProds = OrderedProducts.query.filter(OrderedProducts.OrderId == order.id)

                for ord_prod in orderedProds:
                    if ord_prod.ProductId != product.id or ord_prod.requestedItems == ord_prod.receivedItems or product.availableQuantity == 0:
                        continue

                    if product.availableQuantity > ord_prod.requestedItems - ord_prod.receivedItems:
                        product.availableQuantity -= (ord_prod.requestedItems - ord_prod.receivedItems)
                        ord_prod.receivedItems = ord_prod.requestedItems
                        db.session.commit()
                    else:
                        ord_prod.receivedItems += product.availableQuantity
                        product.availableQuantity = 0
                        db.session.commit()

                leftRequests = OrderedProducts.query.filter(OrderedProducts.OrderId == order.id)

                found = False
                for req in leftRequests:
                    if req.requestedItems != req.receivedItems:
                        found = True
                        break

                if not found:
                    order.status = "F"
                    db.session.commit()


