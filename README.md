# hmlet
hmlet Assignment:

App hosting on : http://prajaktarninave.pythonanywhere.com/

API'S:

1. /hello : 
Testing API to check if server running. 
All operation will be done with content-Type = json.

2. /register : (jwt-authentication)
For all other operations on this App, user first needs to register with below mandatory parameters:
{
	"username":<unique username e.g. "test1@gmail.com" >,
	"password":<password : e.g. "test">,
	"name":<e.g.  "test">
}
response :
On successful registration, user will get "access_token" and "refresh_token" to start further operations. Please store "access_toekn" in Authorization header as :
key : Authorization , Value : Bearer {{access_token}}
All operation will be followed with this access tokens.

3. /login : (jwt-authentication)
User can login with registerd username and password in request body. 
response: 
On successful login, user will get "access_token" and "refreesh_token" to start further operations. Please store "access_toekn" in Authorization header as :
key : Authorization , Value : Bearer {{access_token}}
All operation will be followed with this access tokens.

4. /refresh : (jwt-authentication)
If session has exceeded 15 min (maximum access_token lifetime), access_token will be revoked and will no longer be valid.
Caller need to use refresh_token to fetch new access_token.
key : Authorization , Value : Bearer {{refresh_token}}

5. /logout/access : (jwt-authentication) 
With this API, we can logout. i.e. we cannot do any further operation using access_token, access_token will be revoked on success reponse from api. If we want, we can generate a new access_token using /refresh API.

6. /logout/refresh : (jwt-authentication)
To logout with refresh_token. Once logged out with refresh token, refresh_token will be revoked. Need to login again to get fresh access_token and refresh_token. Once refresh_token revoked, It cannot be use to for /refresh

7. /upload-photo :
It will upload photo provided by logged-in user in body as file parameter in form data :
request-body: form data -> key : file, value : <filename>.png
  
8. /post-photo/<int:photo_id> :
Uploaded photo will be posted.  It can be verified with [GET] /photo/<id> API, checking "posted" field in response set to 1. If its 0, it means photo is still in draft. photo_id can be Obtained from /my-photos API
  
9. /photos/<int:photo_id>/caption :
Edit photo Caption with parameter in body as :
{
  "caption":"12sdjkfh"
}

10. /delete-photo/<int:photo_id> :
Photo with given id will be deleted. id is obtained by `/all-photos` or `/my-photos` apis

11. /all-photos :
This API will provide all photos regardless of which user is logged in. (As in requirement to provide all photos)
To get photos in particular order, Caller need to send order(case insensitive and either `ASC` or `DESC`) in query parameter as :
/all-photos?order=asc
Also, can filter photos based on username as :
/all-photos?user=test1@gmail.com
We can use both order and user query together as well :
/all-photos?order=asc&user=test@gmail.com
Note : All photos will be ordered ASC/DESC based on "published" date.

12. /my-photos :
Only photos owned by logged in user will be retunred in `ASC`/`DESC` order using query parameter:
/my-photos?order=ASC

13. /photo/<int:photo_id> :
Get photo based for given photo_id in path parameter.

14. /my-drafts :
By default, upload photo saves photo as draft.
Returns all drafted photos which are not published.
Drafted photos are idnetified with flag value `posted` = 0 in response.
Can be eaccessed in `ASC`/`DESC` order by using query param.



Config:
All basic configs are stored in config.py file

Databases:

1. sql : 
SQL database is used to store user entries in user table and phot entries in photo table. user password is protected with sha256 algorithm

2. redis :
Redis is used to store blacklisted access_token and refresh_token, so that once user has been logged out, no one else can access user data with these tokens. Redis is being selected since we dont need persistant data. Token can be invalid after standard timestamp for respective token. From redis token will be deleted by using TTL option.
Note : Since there was problem in connecting to Redis in pythonanywhere.com; token will be blacklisted on flash memory. SO if app will be reloded, token still be valid. This is bcause, blacklisted token data is not stored in any database.
If user wants to store blacklisted tokens in redis (if only able to connect to redis db), user can set use_redis key in config.py file to 1.


Installation:
Commands to install packages before running application are in install.sh
Required packages for running this app : 
flask
flask-httpauth
mysql-connector
flask_restful
flask_jwt_extended
passlib
redis



Thanks,
Prajakta







