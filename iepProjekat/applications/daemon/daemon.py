import threading
import redis
from applications.configuration import Configuration
from applications.models import *

class Daemon(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.redis = redis.StrictRedis(host=Configuration.REDIS_HOST, charset="utf-8", decode_responses=True)
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe("warehouseUpdates")

    def run(self):
        while (True):
            for msg in self.pubsub.listen():
                msg = msg['data']
                row = msg.split(',')
                categories = row[0].split('|')
                name = row[1]
                quantity = int(row[2])
                price = float(row[3])
                product = Product.query.filter(name=name).first()
                if not product:
                    product = Product(name=name, availableQuantity=quantity, price=price)
                    db.session.add(product)
                    db.session.commit()

                    for category in categories:
                        cat = Category.query.filter(name=category).first()
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
                    product_categories = ProductCategory.query.filter(ProductId=product.id)

                    pcs = []
                    for pc in product_categories:
                        pcs.append(Category.query.filter(id=pc.CategoryId).first().name)

                    if set(categories) != set(pcs):
                        continue

                    currentQuantity = product.availableQuantity
                    currentPrice = product.price

                    newPrice = (currentQuantity * currentPrice + quantity * price) / currentQuantity + quantity

                    product.price = newPrice
                    product.availableQuantity += quantity
                    db.session.update(product)
                    db.session.commit()



if __name__ == "__main__":
    daemon = Daemon()
    daemon.start()
