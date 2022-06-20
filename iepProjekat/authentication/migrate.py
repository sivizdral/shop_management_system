from flask import Flask
from configuration import Configuration
from flask_migrate import Migrate, init, migrate, upgrade
from models import *
from sqlalchemy_utils import database_exists, create_database

application = Flask(__name__)
application.config.from_object(Configuration)

migrateObject = Migrate(application, db)
if not database_exists(application.config["SQLALCHEMY_DATABASE_URI"]):
    create_database(application.config["SQLALCHEMY_DATABASE_URI"])

db.init_app(application)

with application.app_context() as context:
    init()
    migrate(message="Production migration.")
    upgrade()

    adminRole = Role(name="admin")
    warehousemanRole = Role(name="warehouseman")
    customerRole = Role(name="customer")

    db.session.add(adminRole)
    db.session.add(warehousemanRole)
    db.session.add(customerRole)
    db.session.commit()

    admin = User(forename="admin", surname="admin", email="admin@admin.com", password="1")

    db.session.add(admin)
    db.session.commit()

    userRole = UserRole(userId=admin.id, roleId=adminRole.id)

    db.session.add(userRole)
    db.session.commit()


