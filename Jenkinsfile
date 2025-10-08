pipeline {
    agent any

    environment {
        APP_NAME = 'myapp'
        FRONTEND_DIR = 'frontend'
        BACKEND_DIR = 'backend'
        APP_SERVICE_DIR = 'backend/app_service'
        MODEL_SERVICE_DIR = 'backend/model_service'
    }

    stages {

        stage('Checkout Code') {
            steps {
                echo "📦 Checking out latest code from GitHub"
                checkout scm
            }
        }

        stage('Setup Backend Dependencies') {
            parallel {
                stage('Setup App Service') {
                    steps {
                        echo "📦 Setting up app_service virtual environment"
                        dir("${APP_SERVICE_DIR}") {
                            bat 'uv init --python 3.11.2'
                            bat 'uv add -r requirements.txt'
                        }
                    }
                }
                stage('Setup Model Service') {
                    steps {
                        echo "📦 Setting up model_service virtual environment"
                        dir("${MODEL_SERVICE_DIR}") {
                            bat 'uv init --python 3.11.2'
                            bat 'uv add -r requirements.txt'
                        }
                    }
                }
            }
        }

        stage('Setup Frontend Dependencies') {
            steps {
                echo "📦 Installing frontend dependencies with npm"
                dir("${FRONTEND_DIR}") {
                    bat 'npm install'
                }
            }
        }

        stage('Run Backend Linters') {
            parallel {
                stage('Lint App Service') {
                    steps {
                        echo "🧹 Running Ruff and Black checks on app_service"
                        dir("${APP_SERVICE_DIR}") {
                            bat 'uv run ruff check .'
                            bat 'uv run black --check .'
                        }
                    }
                }
                stage('Lint Model Service') {
                    steps {
                        echo "🧹 Running Ruff and Black checks on model_service"
                        dir("${MODEL_SERVICE_DIR}") {
                            bat 'uv run ruff check .'
                            bat 'uv run black --check .'
                        }
                    }
                }
            }
        }

        stage('Run Frontend Linting') {
            steps {
                echo "🧹 Running ESLint on frontend"
                dir("${FRONTEND_DIR}") {
                    bat 'npm run lint || exit 0'
                }
            }
        }

        stage('Run Backend Tests') {
            steps {
                echo "🧪 Running backend tests with coverage"
                dir("${BACKEND_DIR}") {
                    bat 'cd app_service'
                    bat 'uv run python -m pytest tests/unit/ --cov=. --cov-report=xml:coverage-app.xml --junitxml=test-results-app.xml -v'
                    bat 'cd ..\\model_service'
                    bat 'uv run python -m pytest tests/unit/ --cov=. --cov-report=xml:coverage-model.xml --junitxml=test-results-model.xml -v'
                }
            }
            post {
                always {
                    junit "${APP_SERVICE_DIR}\\test-results-app.xml, ${MODEL_SERVICE_DIR}\\test-results-model.xml"
                    recordCoverage tools: [
                        [parser: 'COBERTURA', pattern: "${APP_SERVICE_DIR}\\coverage-app.xml"],
                        [parser: 'COBERTURA', pattern: "${MODEL_SERVICE_DIR}\\coverage-model.xml"]
                    ]
                }
            }
        }

        stage('Build Frontend') {
            steps {
                echo "🏗️ Building React frontend with Vite"
                dir("${FRONTEND_DIR}") {
                    bat 'npm run build'
                }
            }
        }

        stage('Build Docker Images') {
            when {
                branch 'main'
            }
            parallel {
                stage('Build App Service Image') {
                    steps {
                        echo "🐳 Building Docker image for app_service"
                        dir("${APP_SERVICE_DIR}") {
                            bat "docker build -t %APP_NAME%_app:%GIT_COMMIT% ."
                        }
                    }
                }
                stage('Build Model Service Image') {
                    steps {
                        echo "🐳 Building Docker image for model_service"
                        dir("${MODEL_SERVICE_DIR}") {
                            bat "docker build -t %APP_NAME%_model:%GIT_COMMIT% ."
                        }
                    }
                }
                stage('Build Frontend Image') {
                    steps {
                        echo "🐳 Building Docker image for frontend"
                        dir("${FRONTEND_DIR}") {
                            bat "docker build -t %APP_NAME%_frontend:%GIT_COMMIT% ."
                        }
                    }
                }
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                echo "🚀 Deploying all services"
                bat 'docker-compose -f docker-compose.yml down'
                bat 'set APP_NAME=%APP_NAME%'
                bat 'set GIT_COMMIT=%GIT_COMMIT%'
                bat 'docker-compose -f docker-compose.yml up -d'
            }
        }

    }

    post {
        success {
            echo "✅ Pipeline completed successfully!"
        }
        failure {
            echo "❌ Build failed! Check the logs for details."
        }
        always {
            echo "🧹 Cleaning up workspace"
            cleanWs()
        }
    }
}
