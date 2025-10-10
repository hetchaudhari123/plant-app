pipeline {
    options {
        buildDiscarder(logRotator(numToKeepStr: '2', daysToKeepStr: '14'))
        timestamps()
    }

    agent any

    environment {
        APP_NAME = 'myapp'
        FRONTEND_DIR = 'frontend'
        BACKEND_DIR = 'backend'
        APP_SERVICE_DIR = 'backend/app_service'
        MODEL_SERVICE_DIR = 'backend/model_service'
    }

    stages {
        stage('Debug branch') {
            steps {
                echo "Current branch: ${env.BRANCH_NAME}"
                echo "GIT_BRANCH: ${env.GIT_BRANCH}"
            }
        }
        stage('Setup Environment') {
            steps {
                script {
                    echo "Setting up environment files..."
                    
                    withCredentials([
                        file(credentialsId: 'agri_vision_app_service_env', variable: 'APP_ENV_FILE'),
                        file(credentialsId: 'agri_vision_model_service_env', variable: 'MODEL_ENV_FILE'),
                        file(credentialsId: 'agri_vision_frontend_env', variable: 'FRONTEND_ENV_FILE')
                    ]) {
                        bat '''
                            copy "%APP_ENV_FILE%" "%APP_SERVICE_DIR%/.env"
                            copy "%MODEL_ENV_FILE%" "%MODEL_SERVICE_DIR%/.env"
                            copy "%FRONTEND_ENV_FILE%" "frontend/.env"
                            
                            echo Environment files configured successfully
                        '''
                    }
                }
            }
        }
        stage('Check PATH') {
            steps {
                bat 'echo %PATH%'
            }
        }

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
                            bat '''
                                uv python install 3.11
                                uv init --python 3.11
                                uv add -r requirements.txt --index-strategy unsafe-best-match
                            '''
                        }
                    }
                }
                stage('Setup Model Service') {
                    steps {
                        echo "📦 Setting up model_service virtual environment"
                        dir("${MODEL_SERVICE_DIR}") {
                            bat '''
                                uv python install 3.11
                                uv init --python 3.11

                                REM --- create filtered requirements file without torch packages ---
                                findstr /v /i "torch torchvision torchaudio" requirements.txt > requirements_without_torch.txt

                                

                                uv add -r requirements_without_torch.txt --index-strategy unsafe-best-match

                                REM Install PyTorch CPU separately
                                uv pip install torch==2.3.0+cpu torchvision==0.18.0+cpu torchaudio==2.3.0+cpu --index-url https://download.pytorch.org/whl/cpu
                            '''
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
                            bat '''
                                uv run ruff check .
                                uv run black --check .
                            '''
                        }
                    }
                }
                stage('Lint Model Service') {
                    steps {
                        echo "🧹 Running Ruff and Black checks on model_service"
                        dir("${MODEL_SERVICE_DIR}") {
                            bat '''
                                uv run ruff check .
                                uv run black --check .
                            '''
                        }
                    }
                }
            }
        }

        stage('Run Frontend Linting') {
            steps {
                echo "🧹 Running ESLint on frontend"
                dir("${FRONTEND_DIR}") {
                    bat 'npm run lint'
                }
            }
        }

        stage('Run Backend Tests') {
            parallel {
                stage('Test App Service') {
                    steps {
                        echo "🧪 Running app_service tests with coverage"
                        dir("${APP_SERVICE_DIR}") {
                            bat '''
                                if not exist test-results mkdir test-results
                                uv run python -m pytest tests/unit/ --cov=. --cov-report=xml:test-results/coverage.xml --junitxml=test-results/results.xml -v
                            '''
                        }
                    }
                }
                stage('Test Model Service') {
                    steps {
                        echo "🧪 Running model_service tests with coverage"
                        dir("${MODEL_SERVICE_DIR}") {
                            bat '''
                                if not exist test-results mkdir test-results
                                uv run python -m pytest tests/unit/ --cov=. --cov-report=xml:test-results/coverage.xml --junitxml=test-results/results.xml -v
                            '''
                        }
                    }
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
                bat '''
                    docker-compose -f docker-compose.yml down
                    set APP_NAME=%APP_NAME%
                    set GIT_COMMIT=%GIT_COMMIT%
                    docker-compose -f docker-compose.yml up -d --build
                '''
            }
        }
    }

    post {
        always {
            script {
                script {
                    // Always try to publish, allowEmptyResults handles missing files
                    junit allowEmptyResults: true, testResults: '**/test-results/results.xml'
                    
                    // Check if any coverage file exists before recording
                    def coverageFiles = findFiles(glob: '**/test-results/coverage.xml')
                    if (coverageFiles.length > 0) {
                        recordCoverage tools: [[parser: 'COBERTURA', pattern: '**/test-results/coverage.xml']]
                    }
                }
            }
        }
        success {
            echo "✅ Pipeline completed successfully!"
        }
        failure {
            echo "❌ Build failed! Check the logs for details."
        }
        cleanup {
            echo "🧹 Cleaning up workspace"
            cleanWs()
            
            // bat 'docker system prune -af || true'
        }
    }
}