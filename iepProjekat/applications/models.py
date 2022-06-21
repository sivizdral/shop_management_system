from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class ProductCategory(db.Model):
    __tablename__ = "productcategories"

    id = db.Column(db.Integer, primary_key=True)
    ProductId = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    CategoryId = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)


class OrderedProducts(db.Model):
    __tablename__ = "orderedproducts"

    id = db.Column(db.Integer, primary_key=True)
    OrderId = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    ProductId = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    price = db.Column(db.Float, nullable=False)
    availableQuantity = db.Column(db.Integer, nullable=False)

    categories = db.relationship("Category", secondary=ProductCategory.__table__, back_populates="products")
    orders = db.relationship("Order", secondary=OrderedProducts.__table__, back_populates="orders")


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)

    products = db.relationship("Product", secondary=ProductCategory.__table__, back_populates="categories")


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(1), nullable=False)
    creationTime = db.Column(db.DateTime, nullable=False)

    products = db.relationship("Product", secondary=OrderedProducts.__table__, back_populates="products")
