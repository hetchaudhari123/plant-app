# --- Build stage ---
FROM node:20 AS builder
WORKDIR /app

# Build arguments for Vite environment variables
ARG VITE_API_URL
ARG VITE_MODEL_API_URL

# Set them as environment variables so Vite can pick them up
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_MODEL_API_URL=$VITE_MODEL_API_URL

# Copy package.json and install dependencies
COPY package*.json ./
RUN npm install

# Copy source code
COPY . .

# Build the app (Vite reads the VITE_* env vars here)
RUN npm run build

# --- Production stage ---
FROM nginx:alpine

# Copy build output from Node build stage
COPY --from=builder /app/build /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
