How to run:
For dev:
uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
For prod:
gunicorn -k uvicorn.workers.UvicornWorker app_service:main --bind 0.0.0.0:8000 --workers 4

remove returning token_version 
see the url length



docker build -t app_service .
docker run --env-file .env -p 8000:8000 app_service:latest



docker tag project-app_service hetchaudhari/agri-vision-app-service:latest

docker push hetchaudhari/agri-vision-app-service:latest

# For running tests
uv run python -m pytest tests/unit/test_auth.py -v

# For utf-16 to utf-8
iconv -f UTF-16LE -t UTF-8 ./requirements.txt > ./requirements_tmp.txt && mv ./requirements_tmp.txt ./requirements.txt

