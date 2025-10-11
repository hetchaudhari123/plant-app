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
        stage('Checkout Code') {
            steps {
                echo "📦 Checking out latest code from SCM"
                checkout scm
            }
        }

        stage('Detect Branch') {
            steps {
                script {
                    def detected = bat(
                        script: 'git rev-parse --abbrev-ref HEAD',
                        returnStdout: true
                    ).trim()

                    // handle detached HEAD case
                    if (detected == 'HEAD') {
                        detected = bat(
                            script: 'git branch -r --contains HEAD',
                            returnStdout: true
                        ).trim().tokenize('/').last()
                    }

                    env.BRANCH_NAME = detected
                    echo "✅ Detected branch: ${env.BRANCH_NAME}"
                }
            }
        }

        stage('Setup Environment') {
            steps {
                script {
                    echo "⚙️ Setting up environment files..."
                    withCredentials([
                        file(credentialsId: 'agri_vision_app_service_env_production', variable: 'APP_ENV_PRODUCTION_FILE'),
                        file(credentialsId: 'agri_vision_app_service_env', variable: 'APP_ENV_FILE'),
                        file(credentialsId: 'agri_vision_model_service_env', variable: 'MODEL_ENV_FILE'),
                        file(credentialsId: 'agri_vision_frontend_env', variable: 'FRONTEND_ENV_FILE')
                    ]) {
                        bat '''
                            copy "%APP_ENV_PRODUCTION_FILE%" "%APP_SERVICE_DIR%\\.env.production"
                            copy "%APP_ENV_FILE%" "%APP_SERVICE_DIR%\\.env"
                            copy "%MODEL_ENV_FILE%" "%MODEL_SERVICE_DIR%\\.env"
                            copy "%FRONTEND_ENV_FILE%" "%FRONTEND_DIR%\\.env"
                            echo Environment files configured successfully.
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

        




        stage('Setup Backend Dependencies') {
            parallel {
                stage('Setup App Service') {
                    steps {
                        echo "📦 Installing app_service dependencies"
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
                        echo "📦 Installing model_service dependencies"
                        dir("${MODEL_SERVICE_DIR}") {
                            bat '''
                                uv python install 3.11
                                uv init --python 3.11
                                findstr /v /i "torch torchvision torchaudio" requirements.txt > requirements_without_torch.txt
                                uv add -r requirements_without_torch.txt --index-strategy unsafe-best-match
                                uv pip install torch==2.3.0+cpu torchvision==0.18.0+cpu torchaudio==2.3.0+cpu --index-url https://download.pytorch.org/whl/cpu
                            '''
                        }
                    }
                }
            }
        }

        stage('Setup Frontend Dependencies') {
            steps {
                echo "📦 Installing frontend dependencies"
                dir("${FRONTEND_DIR}") {
                    bat 'npm install'
                }
            }
        }

        stage('Download Torch Models') {
            steps {
                echo "📥 Downloading Torch models into saved_models..."
                dir("${MODEL_SERVICE_DIR}") {
                    bat '''
                    REM Create target folder if it doesn't exist
                    if not exist saved_models mkdir saved_models

                    REM Folder ID (without ?usp=sharing)
                    set FOLDER_ID=1QYhMcjWePAQ-W7S9PT8hB-oUX0RlsX2h

                    REM Download all files from Google Drive folder into saved_models/
                    uv run gdown --folder https://drive.google.com/drive/folders/%FOLDER_ID% -O saved_models
                '''
        }
    }
}


        stage('Run Linters') {
            parallel {
                stage('Lint App Service') {
                    steps {
                        echo "🧹 Linting app_service"
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
                        echo "🧹 Linting model_service"
                        dir("${MODEL_SERVICE_DIR}") {
                            bat '''
                                uv run ruff check .
                                uv run black --check .
                            '''
                        }
                    }
                }

                stage('Lint Frontend') {
                    steps {
                        echo "🧹 Running ESLint on frontend"
                        dir("${FRONTEND_DIR}") {
                            bat 'npm run lint'
                        }
                    }
                }
            }
        }

        stage('Run Tests') {
            parallel {
                stage('App Service Tests') {
                    steps {
                        echo "🧪 Running app_service tests"
                        dir("${APP_SERVICE_DIR}") {
                            bat '''
                                if not exist test-results mkdir test-results
                                uv run python -m pytest tests/unit/ --cov=. --cov-report=xml:test-results/coverage.xml --junitxml=test-results/results.xml -v
                            '''
                        }
                    }
                }

                stage('Model Service Tests') {
                    steps {
                        echo "🧪 Running model_service tests"
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
                echo "🏗️ Building React frontend"
                dir("${FRONTEND_DIR}") {
                    bat 'npm run build'
                }
            }
        }

        stage('Build Docker Images') {
            parallel {
                stage('App Service Image') {
                    steps {
                        echo "🐳 Building Docker image for app_service"
                        dir("${APP_SERVICE_DIR}") {
                            bat "docker build -t %APP_NAME%_app ."
                        }
                    }
                }

                stage('Model Service Image') {
                    steps {
                        echo "🐳 Building Docker image for model_service"
                        dir("${MODEL_SERVICE_DIR}") {
                            bat "docker build -t %APP_NAME%_model ."
                        }
                    }
                }

                stage('Frontend Image') {
                    steps {
                        echo "🐳 Building Docker image for frontend"
                        dir("${FRONTEND_DIR}") {
                            bat "docker build -t %APP_NAME%_frontend ."
                        }
                    }
                }
            }
        }

        stage('Deploy') {
            steps {
                echo "🚀 Deploying all services"
                bat '''
                    docker-compose -f docker-compose.yml down
                    set APP_NAME=%APP_NAME%
                    docker-compose -f docker-compose.yml up -d --build
                '''
            }
        }
    }

    post {
        always {
            script {
                junit allowEmptyResults: true, testResults: '**/test-results/results.xml'
                def coverageFiles = findFiles(glob: '**/test-results/coverage.xml')
                if (coverageFiles.length > 0) {
                    recordCoverage tools: [[parser: 'COBERTURA', pattern: '**/test-results/coverage.xml']]
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
        }
    }
}
