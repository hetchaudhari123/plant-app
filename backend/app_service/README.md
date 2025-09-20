-> Auto Deletion
db_service

Should own the database:

Manage connections

Provide CRUD APIs for other services

Define data models / schemas

Other services (app_service, model_service) never connect to DB directly.

Communication happens over:

HTTP REST (FastAPI endpoints)

gRPC

Message queues (Kafka, RabbitMQ)

app_service

Handles:

Business logic (auth, profile, image-to-3D pipeline)

Requests from clients

Calls db_service APIs to read/write data

Doesn’t know the DB connection details.

model_service

Handles ML models:

Load models

Make predictions

Can also save/load results via db_service API

Doesn’t connect to DB directly either.


How to run:
uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload



To Check delete account at the end