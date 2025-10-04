
  # Agricultural Themed Web App

  This is a code bundle for Agricultural Themed Web App. The original project is available at https://www.figma.com/design/1ay67CcVZCRS0vIEvhS2Tp/Agricultural-Themed-Web-App.

  ## Running the code

  Run `npm i` to install the dependencies.

  Run `npm run dev` to start the development server.
  

  ## Changes to be done
  Handle exception handling in the service function:
  src/services/authService.tsx
  -> Handle loading
  -> Check Countdown for signup, email change
  -> setError might not be required in slice
  # how to docker build
  docker build --build-arg VITE_API_URL=http://app_service:8000 --build-arg VITE_MODEL_API_URL=http://model_service:8002 -t frontend_service:latest .

  docker run --env-file .env -p 3000:80 frontend_service:latest


  docker tag project-frontend hetchaudhari/agri-vision-frontend-service:latest

  docker push hetchaudhari/agri-vision-frontend-service:latest