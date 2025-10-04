# run locally
uv run python -m uvicorn main:app --host 0.0.0.0 --port 8002 --reload

# install torch-cpu
uv pip install torch==2.3.0+cpu torchvision==0.18.0+cpu torchaudio==2.3.0+cpu --index-url https://download.pytorch.org/whl/cpu

# docker build command
docker build -t model_service .

# docker run command
docker run --env-file .env -p 8002:8002 model_service:latest



docker tag project-model_service hetchaudhari/agri-vision-model-service:latest

docker push hetchaudhari/agri-vision-model-service:latest

