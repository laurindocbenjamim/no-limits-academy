

import secrets
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from flask import (jsonify, make_response, request, render_template)

from flask_jwt_extended import (     
    create_access_token,
    jwt_required,
    current_user,
    get_jwt,
    get_jwt_identity,
    set_access_cookies,
    unset_jwt_cookies
)

import jwt
from werkzeug.security import check_password_hash
from app.configs import db
from app.models import User, TokenBlocklist, TokenBlocklist2

def routes(app):

    @app.route('/')
    def index():

        welcome_title = "Welcome to Data Tuning"
        welcome_message = "Empowering learners with cutting-edge online education"
        response = make_response(render_template('home.html', title='Home', welcome_title=welcome_title,  welcome_message=welcome_message))
        return response


    @app.route('/login_without_cookies', methods=['GET', 'POST'])
    def login_without_cookies():

        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        

        user = User.query.filter_by(username=username).one_or_none()
        if not user or not user.check_password(password):
            return jsonify({"error": "Wrong username or password", "user": user.to_dict()}), 401
        # Generate a JWT token
       
        access_token = create_access_token(identity=str(user.id))

        return make_response(jsonify({"secret_key": app.config['SECRET_KEY'], 
                                      "access_token": access_token,
                                      "username": username
                                      }),200)
    
    # Login with cookie
    @app.route('/login-w-cookies', methods=['GET', 'POST'])
    def login_with_cookies():
        response = jsonify({"msg": "login successful"}), 200
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        

        user = User.query.filter_by(username=username).one_or_none()
        if not user or not user.check_password(password):
            return jsonify({"error": "Wrong username or password", "user": user.to_dict()}), 401
        # Generate a JWT token
       
        access_token = create_access_token(identity=str(user.id))

        response = make_response(jsonify({"status_code": 200,
                                      "username": username
                                      }),200)
        set_access_cookies(response, access_token)
        return response
    
    # Logout with cookies
    @app.route("/logout_with_cookies", methods=["GET", "POST"])
    def logout_with_cookies():
        response = jsonify({'msg':"logout successful", 'status_code':200})
        unset_jwt_cookies(response)
        return response

    # Endpoint for revoking the current users access token. Saved the unique
    # identifier (jti) for the JWT into our database.
    @app.route("/logout-with-revoking-token", methods=["GET", "POST"])
    @jwt_required()
    def modify_token():
        jti = get_jwt()["jti"]
        now = datetime.now(timezone.utc)
        block_list=None
        try:
            block_list = TokenBlocklist2(jti=jti, created_at=now)
            db.session.add(block_list)
            db.session.commit()
        except Exception as e:
            return jsonify(error=str(e))
        response = jsonify(msg="JWT revoked", time=now, jtid=jti, block_list=block_list.to_dict())
        #unset_jwt_cookies(response)
        return response

    @app.route("/logout_with_revoking_token_2", methods=["get", "post"])
    @jwt_required(verify_type=False)
    def modify_token_2():
        token = get_jwt()
        jti = token["jti"]
        ttype = token["type"]
        now = datetime.now(timezone.utc)
        block_list=None

        try:
            block_list = TokenBlocklist(jti=jti, type=ttype, created_at=now)
            db.session.add(block_list)
            db.session.commit()
            response = jsonify(msg=f"{ttype.capitalize()} token successfully revoked", logout="Your session has been terminated!", block_list=block_list.to_dict())
        except Exception as e:
            return jsonify(error=str(e))        
        
        #unset_jwt_cookies(response)
        return response


    @app.route('/protected', methods=['GET'])
    @jwt_required()
    def ptotected():
        
        claims = get_jwt()
        response = make_response(jsonify(
            status_code=200,
            foo="bar",
            message="Welcome to protected route!",
            claims=claims,
            id=current_user.id,
            full_name=current_user.full_name,
            username=current_user.username,
            ), 200)

        return response

    @app.route("/only_headers")
    @jwt_required(locations=["headers"])
    def only_headers():
        return jsonify(foo="baz")

    @app.route('/test-token', methods=['POST'])
    def test_jwt_token():
        data = request.get_json()

        token = data.get('token')

        # Replace this with the token generated in Flask
        if(not token):
            return f"Token is required!"

        # Replace with the same secret key you used in Flask

        try:
            decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            return jsonify({'token_received': token, 'decoded': decoded})
        except jwt.ExpiredSignatureError as e:
            return f"❌ Token has expired {str(e)}"
        except jwt.InvalidTokenError as e:
            return f"❌ Token is invalid {str(e)}"

    @app.route('/secret-key/gen')
    def generate_secret_key():
        secret_key = secrets.token_urlsafe(64)
        return jsonify(SECRET_KEY=secret_key)