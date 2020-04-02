# application config
MAX_PHOTO_SIZE = 16 * 1024 * 1024

# db config
dbhost = "prajaktarninave.mysql.pythonanywhere-services.com"
dbuser = "prajaktarninave"
dbpassword = "Praju+_123"
dbname = "prajaktarninave$hmlet_db"

# redis config
use_redis = 0  # 0->False. Not using Redis  and 1->True. using redis
redis_host = "localhost"
redis_port = 6379
time_to_expire_redis_key = 60*60*24  # one day
