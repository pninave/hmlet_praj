#!/usr/local/bin/python3.7
import mysql.connector as mysql
from datetime import datetime
import redis

from config import dbhost, dbuser, dbpassword, dbname,\
    time_to_expire_redis_key, use_redis, redis_host, redis_port


dbNew = mysql.connect(
    host=dbhost,
    user=dbuser,
    passwd=dbpassword,
    database=dbname
)
cursor_db = dbNew.cursor()

if use_redis:
    rconn = redis.Redis(host=redis_host, port=redis_port, db=0)
else:
    blacklist = set()


def create_tables():

    # photo table
    sql_create_photo_table = "CREATE TABLE IF NOT EXISTS photos (\
                                    id INT AUTO_INCREMENT,\
                                    userid INT NOT NULL,\
                                    is_posted BOOLEAN NOT NULL DEFAULT false,\
                                    is_deleted BOOLEAN NOT NULL DEFAULT false,\
                                    url VARCHAR(512) NOT NULL,\
                                    caption VARCHAR(512) DEFAULT NULL,\
                                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,\
                                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,\
                                    published_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,\
                                    PRIMARY KEY (`id`)\
                                    );"
    # users table
    sql_create_user_table = "CREATE TABLE IF NOT EXISTS users (\
                                    id INT AUTO_INCREMENT,\
                                    email VARCHAR(32) NOT NULL,\
                                    username VARCHAR(32) NOT NULL,\
                                    password VARCHAR(512) NOT NULL,\
                                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,\
                                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,\
                                    PRIMARY KEY (`id`),\
                                    UNIQUE KEY (`email`)\
                                    );"

    cursor_db.execute(sql_create_photo_table)
    cursor_db.execute(sql_create_user_table)
    dbNew.commit()
    cursor_db.execute("SHOW TABLES")
    tables = cursor_db.fetchall()
    print("Tables Created ...")
    for table in tables:
        print(table)


def insert_user(email, password, name):
    try:
        q = "INSERT INTO users (email, password, username) VALUES(%s,%s,%s)"
        val = (email, password, name)
        cursor_db.execute(q, val)
        dbNew.commit()
        return True
    except mysql.IntegrityError as err:
        print(err)
        return False
    except Exception as e:
        print(e)
        return False


def user_exist(email):
    try:
        q = "SELECT `email` FROM users WHERE `email` = '" + str(email) + "'"
        cursor_db.execute(q)
        result = cursor_db.fetchone()
        # print(result)
        return True
    except Exception as e:
        print(e)
        return False


def get_pwd(email):
    try:
        q = "SELECT `password` FROM users WHERE `email` = '" + str(email) + "'"
        cursor_db.execute(q)
        result = cursor_db.fetchone()
        # print(result)
        return result[0] if result else None
    except Exception as e:
        print(e)
        return None


def fetch_userid(email):
    try:
        q = "SELECT `id` FROM users WHERE `email` = '" + str(email) + "'"
        cursor_db.execute(q)
        result = cursor_db.fetchone()
        return result[0] if result else None
    except Exception as e:
        print(e)
        return None


def fetch_photoid(userid, photo_id):
    try:
        q = "SELECT `id` FROM photos WHERE `userid` = '" + \
            str(userid) + "' AND `id` = '" + \
            str(photo_id) + "' AND `is_deleted` = 0"
        cursor_db.execute(q)
        result = cursor_db.fetchone()
        if not result:
            return None
        return result[0] if result else None
    except Exception as e:
        print(e)
        return None


def convert_to_photo_obj(res):
    data = dict()
    data = {
        "id": res[0],
        "userid": res[1],
        "posted": res[2],
        "deleted": res[3],
        "url": res[4],
        "caption": res[5],
        "created_at": res[6],
        "updates_at": res[7],
        "published_at": res[8]
    }
    return data


def add_user_photos(email, url):
    try:
        userid = fetch_userid(email)
        q = "INSERT INTO photos (userid, url) VALUES(%s,%s)"
        val = (userid, url)
        cursor_db.execute(q, val)
        dbNew.commit()
        last_insert_id = cursor_db.lastrowid
        return last_insert_id
    except Exception as e:
        return e


def edit_user_photo(userid, photo_id, caption):
    try:
        q = "UPDATE photos SET `caption` = '" + str(caption) + "' where `userid` = " + \
            str(userid) + " AND `id` = " + \
            str(photo_id) + " AND `is_deleted` = 0"
        cursor_db.execute(q)
        dbNew.commit()
        return True
    except Exception as e:
        print(e)
        return False


def post_user_photo(userid, photo_id):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        q = "UPDATE photos SET `is_posted` = 1, `published_at` = '" + now + "' where `userid` = " + \
            str(userid) + " AND `id` = " + \
            str(photo_id) + " AND `is_deleted` = 0"
        cursor_db.execute(q)
        dbNew.commit()
        return True
    except Exception as e:
        print(e)
        return False


def delete_user_photo(userid, photo_id):
    try:
        q = "SELECT `url` FROM photos WHERE `userid` = '" + \
            str(userid) + "' AND `id` = '" + str(photo_id) + "'"
        cursor_db.execute(q)
        result = cursor_db.fetchone()

        q = "UPDATE photos SET `is_deleted` = 1 where `userid` = " + \
            str(userid) + " AND `id` = " + \
            str(photo_id) + " AND `is_deleted` = 0"

        cursor_db.execute(q)
        dbNew.commit()
        return result[0] if result else None
    except Exception as e:
        print(e)
        return e


def get_all_photos(order):
    try:
        q = "SELECT * FROM photos where `is_deleted` = 0 order by `published_at` " + order
        cursor_db.execute(q)
        result = cursor_db.fetchall()
        output = []
        for res in result:
            output.append(convert_to_photo_obj(res))
        return output
    except Exception as e:
        print("error all p : ", e)
        return e


def get_my_photos(userid, order):
    try:
        q = "SELECT * FROM photos where `userid` = " + \
            str(userid) + " AND `is_deleted` = 0 order by `published_at` " + order
        cursor_db.execute(q)
        result = cursor_db.fetchall()
        output = []
        for res in result:
            output.append(convert_to_photo_obj(res))
        return output
    except Exception as e:
        print("error all p : ", e)
        return e


def get_photo(userid, photoid):
    try:
        q = "SELECT * FROM photos where `userid` = " + \
            str(userid) + " AND `id` = " + \
            str(photoid) + " AND `is_deleted` = 0"

        cursor_db.execute(q)
        result = cursor_db.fetchone()
        output = {}
        if result:
            output = convert_to_photo_obj(result)
        return output
    except Exception as e:
        print(e)
        return e


def get_draft_photo(userid, order):
    try:
        q = "SELECT * FROM photos where `userid` = " + \
            str(userid) + " AND `is_posted` = 0  AND `is_deleted` = 0 order by `published_at` " + order

        cursor_db.execute(q)
        result = cursor_db.fetchall()
        output = []
        for res in result:
            output.append(convert_to_photo_obj(res))
        return output
    except Exception as e:
        print(e)
        return e


def add_to_redis(key, value):
    try:
        if use_redis:
            rconn.set(key, value)
            rconn.expire(key, time_to_expire_redis_key)
    except Exception as e:
        return {'Error': str(e)}, 400
