How to run:
For dev:
uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
For prod:
gunicorn -k uvicorn.workers.UvicornWorker app_service:main --bind 0.0.0.0:8000 --workers 4
