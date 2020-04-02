rm -rf newvenv
python3.7 -m venv newvenv
source newvenv/bin/activate

echo 'virtual env created...'
echo 'installing... flask'
pip install flask
echo 'installing... flask-httpauth'
pip install flask-httpauth
echo 'installing... mysql-connector'
pip install mysql-connector
echo 'installing... flask_restful'
pip install flask_restful
echo 'installing... flask_jwt_extended'
pip install flask_jwt_extended
echo 'installing... passlib'
pip install passlib
echo 'installing... redis'
pip install redis

echo 'installation success for all packages.'
