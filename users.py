import os
import dbCalls
from passlib.hash import pbkdf2_sha256 as sha256
from flask import jsonify
from flask_restful import Resource, reqparse
from flask_jwt_extended import create_access_token, create_refresh_token,\
    get_jwt_identity, get_raw_jwt

baseDir = os.getcwd()
photoDir = baseDir + "/photos"
blacklist = set()

try:
    if not os.path.exists(photoDir):
        os.makedirs(photoDir)
        print("Successfully created the directory %s " % photoDir)
    else:
        print("%s Already Exists." % photoDir)
except OSError:
    print("Creation of the directory %s failed.." % photoDir)


def generate_password(password):
    return sha256.hash(password)


def verify_password(password, hash):
    return sha256.verify(password, hash)


def registration(username, password, name):
    if dbCalls.fetch_userid(username):
        e = {'Error': 'User {} already exists'.format(username)}
        resp = jsonify(e)
        resp.status_code = 400
        return resp
    try:
        password = generate_password(password)
        success = dbCalls.insert_user(username, password, name)
        if not success:
            e = {"Error": "Failure in creating Entry in DB for User"}
            resp = jsonify(e)
            resp.status_code = 400
            return resp

        access_token = create_access_token(identity=username)
        refresh_token = create_refresh_token(identity=username)

        try:
            userDir = photoDir + "/" + username
            if not os.path.exists(userDir):
                os.makedirs(userDir)
        except OSError:
            e = {"Error": "Failure in creating Directory for User"}
            resp = jsonify(e)
            resp.status_code = 400
            return resp
        msg = {
            'message': 'User {} created'.format(username),
            'access_token': access_token,
            'refresh_token': refresh_token
        }
        resp = jsonify(msg)
        resp.status_code = 201
        return resp
    except:
        e = {'Error': 'Something went wrong'}
        resp = jsonify(e)
        resp.status_code = 500
        return resp


def login(username, password):
    current_userid = dbCalls.fetch_userid(username)
    if not current_userid:
        return {'Error': 'User {} doesn\'t exist'.format(username)}, 400

    if verify_password(password, dbCalls.get_pwd(username)):
        access_token = create_access_token(identity=username)
        refresh_token = create_refresh_token(identity=username)
        return {
            'message': 'Logged in as {}'.format(username),
            'access_token': access_token,
            'refresh_token': refresh_token
        }, 200
    else:
        return {'Error': 'Wrong credentials'}, 400


def refresh():
    try:
        current_user = get_jwt_identity()
        ret = {
            'access_token': create_access_token(identity=current_user)
        }
        return jsonify(ret), 200

    except Exception as e:
        resp = jsonify({'Error': str(e)})
        resp.status_code = 400
        return resp


def logout_access():
    try:
        jti = get_raw_jwt()['jti']
        if dbCalls.use_redis:
            current_user = get_jwt_identity()
            dbCalls.add_to_redis(jti, current_user)
        else:
            dbCalls.blacklist.add(jti)
        return jsonify({"message": "Successfully logged out with access Token"}), 200
    except Exception as e:
        resp = jsonify({'Error': str(e)})
        resp.status_code = 400
        return resp


def logout_refresh():
    try:
        jti = get_raw_jwt()['jti']
        if dbCalls.use_redis:
            current_user = get_jwt_identity()
            dbCalls.add_to_redis(jti, current_user)
        else:
            dbCalls.blacklist.add(jti)
        return jsonify({"message": "Successfully logged out with refresh Token"}), 200
    except Exception as e:
        resp = jsonify({'Error': str(e)})
        resp.status_code = 400
        return resp
