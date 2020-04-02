#!/usr/local/bin/python3.7
from flask import Flask, request, jsonify
from flask_jwt_extended import (
    JWTManager, jwt_required, jwt_refresh_token_required, get_jwt_identity)
from werkzeug.utils import secure_filename
import os
import dbCalls
import users
import subprocess
from config import MAX_PHOTO_SIZE, use_redis


# # A very simple Flask Hello World app for you to get started with...

# from flask import Flask

# app = Flask(__name__)

# @app.route('/')
# def hello_world():
#     return 'Hello from Flask!'

UPLOAD_FOLDER = '/tmp/'
ALLOWED_EXTENSIONS = set(['pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
jwt = JWTManager(app)
dbCalls.create_tables()

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_PHOTO_SIZE  # Max photo size 16 MB
app.config['JWT_SECRET_KEY'] = 'jwt-photo-app'
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
blacklist = set()


@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    jti = decrypted_token['jti']
    if use_redis:
        blacklisted = dbCalls.rconn.get(jti)
        return blacklisted != None
    else:
        return jti in dbCalls.blacklist


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/hello', methods=['GET'])
def hello():
    try:
        resp = jsonify({"message": "Hello Users. Please Login !!"})
        resp.status_code = 200
        return resp
    except Exception as e:
        resp = jsonify({'Error': str(e)})
        resp.status_code = 400
        return resp


@app.route('/register', methods=['POST'])
def register():
    try:
        if not request.json or ('username' not in request.json) or ('password' not in request.json) or ('name' not in request.json):
            e = "username, password and name are mandatory fields to create user."
            resp = jsonify({'Error': str(e)})
            resp.status_code = 400
            return resp

        if not len(request.json['username']) or not len(request.json['password']) or not len(request.json['name']):
            e = "invalid paramerts for user registration."
            resp = jsonify({'Error': str(e)})
            resp.status_code = 400
            return resp

        if len(request.json['username']) > 32 or len(request.json['password']) > 32 or len(request.json['name']) > 32:
            e = "input paramerts too long."
            resp = jsonify({'Error': str(e)})
            resp.status_code = 400
            return resp

        # username is unique key like email
        username = request.json['username']
        password = request.json['password']
        name = request.json['name']
        return users.registration(username, password, name)

    except Exception as e:
        resp = jsonify({'Error': str(e)})
        resp.status_code = 400
        return resp


@app.route('/login', methods=['POST'])
def login():
    try:
        if not request.json or ('username' not in request.json) or ('password' not in request.json):
            e = "username and password are mandatory fields to create user."
            resp = jsonify({'Error': str(e)})
            resp.status_code = 400
            return resp

        if not len(request.json['username']) or not len(request.json['password']):
            e = "invalid paramerts for user login."
            resp = jsonify({'Error': str(e)})
            resp.status_code = 400
            return resp

        username = request.json['username']
        password = request.json['password']
        return users.login(username, password)

    except Exception as e:
        resp = jsonify({'Error': str(e)})
        resp.status_code = 400
        return resp


@app.route('/refresh', methods=['POST'])
@jwt_refresh_token_required
def refresh():
    try:
        return users.refresh()
    except Exception as e:
        resp = jsonify({'Error': str(e)})
        resp.status_code = 400
        return resp


@app.route('/logout/access', methods=['DELETE'])
@jwt_required
def logout_access():
    try:
        return users.logout_access()
    except Exception as e:
        resp = jsonify({'Error': str(e)})
        resp.status_code = 400
        return resp


@app.route('/logout/refresh', methods=['DELETE'])
@jwt_refresh_token_required
def logout_refresh():
    try:
        return users.logout_refresh()
    except Exception as e:
        resp = jsonify({'Error': str(e)})
        resp.status_code = 400
        return resp


@app.route('/upload-photo', methods=['POST'])
@jwt_required
def upload_photo():
    current_user = users.get_jwt_identity()
    if 'file' not in request.files:
        resp = jsonify({'Error': 'No file part in the request'})
        resp.status_code = 400
        return resp
    file = request.files['file']
    if file.filename == '':
        resp = jsonify({'Error': 'No file selected for uploading'})
        resp.status_code = 400
        return resp
    if file and allowed_file(file.filename):
        # file_size = len(file.read())
        try:
            filename = secure_filename(file.filename)
            upload_dir = users.photoDir + "/" + current_user + "/"
            if os.path.isfile(upload_dir+filename):
                resp = jsonify({'Error': "File already Uploaded."})
                resp.status_code = 400
                return resp

            url = upload_dir+filename
            result = dbCalls.add_user_photos(current_user, url)
            app.config['UPLOAD_FOLDER'] = upload_dir
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            resp = jsonify({"id": result})
            resp.status_code = 201
            return resp
        except Exception as e:
            resp = jsonify({'Error': str(e)})
            resp.status_code = 400
            return resp
    else:
        resp = jsonify(
            {'Error': 'Allowed file types are txt, pdf, png, jpg, jpeg, gif'})
        resp.status_code = 400
        return resp


@app.route('/post-photo/<int:photo_id>', methods=['POST'])
@jwt_required
def post_photo(photo_id):
    try:
        userid = dbCalls.fetch_userid(users.get_jwt_identity())
        photoid = dbCalls.fetch_photoid(userid, photo_id)
        if not photoid:
            resp = jsonify({'Error': "Given photo id Doesnot exists"})
            resp.status_code = 400
            return resp
        res = dbCalls.post_user_photo(userid, photo_id)

        if res:
            resp = jsonify({'message': 'Photo successfully Posted'})
            resp.status_code = 201
            return resp
    except Exception as e:
        resp = jsonify({'message': str(e)})
        resp.status_code = 400
        return resp


@app.route('/photos/<int:photo_id>/caption', methods=['PUT'])
@jwt_required
def edit_photo_caption(photo_id):
    try:
        userid = dbCalls.fetch_userid(users.get_jwt_identity())
        photoid = dbCalls.fetch_photoid(userid, photo_id)
        if not photoid:
            resp = jsonify({'Error': "Given photo id Doesnot exists"})
            resp.status_code = 400
            return resp

        if not request.json or 'caption' not in request.json or not len(request.json['caption']):
            resp = jsonify({'Error': "caption is missing"})
            resp.status_code = 400
            return resp

        caption = request.json['caption']

        res = dbCalls.edit_user_photo(userid, photo_id, caption)

        if res:
            resp = jsonify({'message': 'Photo Caption successfully Updated'})
            resp.status_code = 201
            return resp
    except Exception as e:
        resp = jsonify({'message': str(e)})
        resp.status_code = 400
        return resp


@app.route('/delete-photo/<int:photo_id>', methods=['DELETE'])
@jwt_required
def delete_photo(photo_id):
    try:
        userid = dbCalls.fetch_userid(users.get_jwt_identity())
        photoid = dbCalls.fetch_photoid(userid, photo_id)
        if not photoid:
            resp = jsonify({'Error': "Given photo id Doesnot exists"})
            resp.status_code = 400
            return resp
        deletedFile = dbCalls.delete_user_photo(userid, photo_id)

        if deletedFile:
            if os.path.exists(deletedFile):
                os.remove(deletedFile)
            else:
                resp = jsonify({'message': 'Photo already Deleted'})
                resp.status_code = 400
                return resp
            resp = jsonify({'message': 'Photo successfully Deleted'})
            resp.status_code = 200
            return resp

    except Exception as e:
        resp = jsonify({'message': str(e)})
        resp.status_code = 400
        return resp


@app.route('/all-photos', methods=['GET'])
@jwt_required
def all_photos():
    try:
        user = request.args.get('user')
        order = request.args.get('order')
        if 'order' not in request.args:
            order = "ASC"

        if not len(order) or (order.upper() not in ["ASC", "DESC"]):
            resp = jsonify(
                {'Error': 'invalid order, must be one of asc or desc'})
            resp.status_code = 400
            return resp

        if user:
            userid = dbCalls.fetch_userid(user)
            if not userid:
                return {'Error': 'User {} doesn\'t exist'.format(user)}, 400
            photos = dbCalls.get_my_photos(userid, order)
        else:
            photos = dbCalls.get_all_photos(order)
        resp = jsonify({'photos': photos})
        resp.status_code = 200
        return resp
    except Exception as e:
        resp = jsonify({'message': str(e)})
        resp.status_code = 400
        return resp


@app.route('/my-photos', methods=['GET'])
@jwt_required
def my_photos():
    try:
        order = request.args.get('order')
        if 'order' not in request.args:
            order = "ASC"

        if not len(order) or (order.upper() not in ["ASC", "DESC"]):
            resp = jsonify(
                {'Error': 'invalid order, must be one of asc or desc'})
            resp.status_code = 400
            return resp

        userid = dbCalls.fetch_userid(users.get_jwt_identity())
        photos = dbCalls.get_my_photos(userid, order)
        resp = jsonify({'photos': photos})
        resp.status_code = 200
        return resp
    except Exception as e:
        resp = jsonify({'message': str(e)})
        resp.status_code = 400
        return resp


@app.route('/photo/<int:photo_id>', methods=['GET'])
@jwt_required
def get_photo(photo_id):
    try:
        userid = dbCalls.fetch_userid(users.get_jwt_identity())
        photoid = dbCalls.fetch_photoid(userid, photo_id)
        if not photoid:
            resp = jsonify({'Error': "Given photo id Doesnot exists"})
            resp.status_code = 400
            return resp

        photo = dbCalls.get_photo(userid, photoid)
        resp = jsonify(photo)
        resp.status_code = 200
        return resp
    except Exception as e:
        resp = jsonify({'message': str(e)})
        resp.status_code = 400
        return resp


@app.route('/my-drafts', methods=['GET'])
@jwt_required
def my_drafts():
    try:
        order = request.args.get('order')
        if 'order' not in request.args:
            order = "ASC"

        if not len(order) or (order.upper() not in ["ASC", "DESC"]):
            resp = jsonify(
                {'Error': 'invalid order, must be one of asc or desc'})
            resp.status_code = 400
            return resp

        userid = dbCalls.fetch_userid(users.get_jwt_identity())
        photos = dbCalls.get_draft_photo(userid, order)
        resp = jsonify({'photos': photos})
        resp.status_code = 200
        return resp
    except Exception as e:
        resp = jsonify({'message': str(e)})
        resp.status_code = 400
        return resp


@app.route('/')
def hello_world():
    return 'Hello from Flask!'
