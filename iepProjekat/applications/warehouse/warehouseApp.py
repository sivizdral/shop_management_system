from flask import Flask;
from applications.configuration import Configuration;
from applications.models import database, Thread;
from redis import Redis;
from adminDecorator import roleCheck;
from flask_jwt_extended import JWTManager;

application = Flask ( __name__ );
application.config.from_object ( Configuration )
jwt = JWTManager ( application );

@application.route ( "/threads", methods = ["GET"] )
@roleCheck ( role = "admin" )
def getThreadsPendingApproval ( ):
    with Redis ( host = Configuration.REDIS_HOST ) as redis:
        bytesList = redis.lrange ( Configuration.REDIS_THREADS_LIST, 0, 0 );
        if ( len ( bytesList ) != 0 ):
            title = bytesList[0].decode ( "utf-8" );
            return title;
        else:
            return "No threads pending approval";

@application.route ( "/threads/approve", methods = ["GET"] )
def approveThreadProposal ( ):
    with Redis ( host = Configuration.REDIS_HOST ) as redis:
        bytes = redis.lpop ( Configuration.REDIS_THREADS_LIST );
        title = bytes.decode ( "utf-8" );
        thread = Thread ( title = title );
        database.session.add ( thread );
        database.session.commit ( );

        bytesList = redis.lrange ( Configuration.REDIS_THREADS_LIST, 0, 0 );
        if ( len ( bytesList ) != 0 ):
            title = bytesList[0].decode ( "utf-8" );
            return title;
        else:
            return "No threads pending approval";

@application.route ( "/threads/decline", methods = ["GET"] )
def declineThreadProposal ( ):
    with Redis ( host = Configuration.REDIS_HOST ) as redis:
        redis.lpop ( Configuration.REDIS_THREADS_LIST );

        bytesList = redis.lrange ( Configuration.REDIS_THREADS_LIST, 0, 0 );
        if ( len ( bytesList ) != 0 ):
            title = bytesList[0].decode ( "utf-8" );
            return title;
        else:
            return "No threads pending approval";


if (__name__ == "__main__"):
    database.init_app ( application );
    application.run ( debug = True, port = 5001 );
