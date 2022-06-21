from functools import wraps
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, get_jwt_identity, verify_jwt_in_request
from flask import jsonify


def isWarehouseman(role):
    def warehousemanDecorator(func):
        @wraps(func)
        def decorator(*arguments, **keywordArguments):
            verify_jwt_in_request()
            claims = get_jwt()
            if "roles" in claims:
                if role in claims["roles"]:
                    return func(*arguments, **keywordArguments)
                else:
                    ret = {"msg": "Missing Authorization Header"}
                    return jsonify(ret), 401
            else:
                ret = {"msg": "Missing Authorization Header"}
                return jsonify(ret), 401
        return decorator
    return warehousemanDecorator
