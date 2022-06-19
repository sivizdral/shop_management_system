from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import db, User, UserRole
from email.utils import parseaddr
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, get_jwt_identity, verify_jwt_in_request
from sqlalchemy import and_
import re
from functools import wraps

application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)

@application.route("/register", methods = ["POST"])
def register():
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")
    email = request.json.get("email", "")
    password = request.json.get("password", "")
    isCustomer = request.json.get("isCustomer", "")

    forenameEmpty = len(forename) == 0
    surnameEmpty = len(surname) == 0
    emailEmpty = len(email) == 0
    passwordEmpty = len(password) == 0
    isCustomerEmpty = isCustomer == ""

    message = ""

    if forenameEmpty:
        message = "Field forename is missing."
    elif surnameEmpty:
        message = "Field surname is missing."
    elif emailEmpty:
        message = "Field email is missing."
    elif passwordEmpty:
        message = "Field password is missing."
    elif isCustomerEmpty:
        message = "Field isCustomer is missing."

    if message != "":
        return Response(message, status = 400)

    validEmail = parseaddr(email)
    if len(validEmail[1]) == 0:
        return Response("Invalid email.", status = 400)

    invalidPass = False
    if len(password) < 8:
        invalidPass = True
    elif re.search(r'[a-z]', password) == False:
        invalidPass = True
    elif re.search(r'[A-Z]', password) == False:
        invalidPass = True
    elif re.search(r'\d', password) == False:
        invalidPass = True
    
    if invalidPass:
        return Response("Invalid password.", status = 400)

    userExists = User.query.filter(User.email == email).first()
    if userExists:
        return Response("Email already exists.", status = 400)
    else:
        newUser = User(forename=forename, surname=surname, password=password, email=email)
        db.session.add(newUser)
        db.session.commit()

        if isCustomer == False:
            newUserRole = UserRole(userId=newUser.id, roleId=3)
            db.session.add(newUserRole)
            db.session.commit()
        else:
            newUserRole = UserRole(userId=newUser.id, roleId=2)
            db.session.add(newUserRole)
            db.session.commit()

        return Response(status=200)


@application.route("/login", methods = ["POST"])
def login():
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    emailEmpty = len(email) == 0
    passwordEmpty = len(password) == 0

    message = ""

    if emailEmpty:
        message = "Field email is missing."
    elif passwordEmpty:
        message = "Field password is missing."

    if message != "":
        return Response(message, status = 400)

    validEmail = parseaddr(email)
    if len(validEmail[1]) == 0:
        return Response("Invalid email.", status = 400)

    user = User.query.filter(User.email == email).first()
    if not user or user.password != password:
        return Response("Invalid credentials.", status = 400)

    additionalClaims = {
        "forename": user.forename,
        "surname": user.surname,
        "roles": [str(role) for role in user.roles]
    }

    accessToken = create_access_token(identity=user.email, additional_claims=additionalClaims)
    refreshToken = create_refresh_token(identity=user.email, additional_claims=additionalClaims)

    return jsonify(accessToken=accessToken, refreshToken=refreshToken)

def isAdmin(role):
    def adminDecorator(func):
        @wraps(func)
        def decorator(*arguments, **keywordArguments):
            verify_jwt_in_request()
            claims = get_jwt()
            if "roles" in claims:
                if role in claims["roles"]:
                    return func(*arguments, **keywordArguments)
                else:
                    ret = {"msg":"Missing Authorization Header"}
                    return jsonify(ret), 401
            else:
                ret = {"msg":"Missing Authorization Header"}
                return jsonify(ret), 401
        return decorator
    return adminDecorator

@application.route("/refresh", methods = ["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    refreshClaims = get_jwt()

    additionalClaims = {
        "forename": refreshClaims["forename"],
        "surname": refreshClaims["surname"],
        "roles": refreshClaims["roles"]
    }

    return Response(create_access_token(identity=identity, additional_claims=additionalClaims), status = 200)

@application.route("/delete", methods = ["POST"])
@isAdmin(role='admin')
def delete():
    email = request.json.get("email", "")

    emailEmpty = len(email) == 0

    if (emailEmpty):
        return Response("Field email is missing.", status = 400)

    validEmail = parseaddr(email)
    if len(validEmail[1]) == 0:
        return Response("Invalid email.", status = 400)

    user = User.query.filter(User.email == email).first()
    if not user:
        return Response("Unknown user.", status = 400)
    else:
        db.session.delete(user)
        db.session.commit()
        return Response(status = 200)
    

if(__name__ == "__main__"):
    db.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5002)  