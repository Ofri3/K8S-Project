pipeline {
    agent {
        // Use the Kubernetes pod template for the agent
        kubernetes {
            yaml """
            apiVersion: v1
            kind: Pod
            spec:
              containers:
              - name: jenkins-agent-cont
                image: ofriz/k8sproject:jenkins-agent-latest
                command:
                - cat
                tty: true
            """
        }
    }

    options {
        // Keeps builds for the last 30 days.
        buildDiscarder(logRotator(daysToKeepStr: '30'))
        // Prevents concurrent builds of the same pipeline.
        disableConcurrentBuilds()
        // Adds timestamps to the log output.
        timestamps()
    }

    environment {
        // Define environment variables
        TELEGRAM_TOKEN = credentials('TELEGRAM_TOKEN')
        APP_IMAGE_NAME = 'app-image'
        WEB_IMAGE_NAME = 'web-image'
        DOCKER_COMPOSE_FILE = 'compose.yaml'
        DOCKER_REPO = 'ofriz/k8sproject'
        DOCKERHUB_CREDENTIALS = 'dockerhub'
        SNYK_API_TOKEN = 'SNYK_API_TOKEN'
    }

    stages {
        stage('Checkout and Extract Git Commit Hash') {
            steps {
                // Checkout code
                checkout scm

                // Extract Git commit hash
                script {
                    bat(script: 'git rev-parse --short HEAD > gitCommit.txt')
                    def GITCOMMIT = readFile('gitCommit.txt').trim()
                    env.GIT_TAG = "${GITCOMMIT}"

                    // Set IMAGE_TAG as an environment variable
                    env.IMAGE_TAG = "v1.0.0-${BUILD_NUMBER}-${GIT_TAG}"
                }
            }
        }
        stage('Build Docker Image') {
            steps {
                script {
                    // Build Docker image using docker-compose
                    bat """
                        docker-compose -f ${DOCKER_COMPOSE_FILE} build
                    """
                }
            }
        }
        stage('Install Python Requirements') {
            steps {
                script {
                    // Install Python dependencies
                    bat """
                        pip install --upgrade pip
                        pip install pytest unittest2 pylint flask telebot Pillow loguru matplotlib
                    """
                }
            }
        }
        stage('Static Code Linting and Unittest') {
            parallel {
                stage('Static code linting') {
                    steps {
                        script {
                            // Run python code analysis
                            bat """
                                python -m pylint -f parseable --reports=no polybot/*.py > pylint.log
                                type pylint.log
                            """
                        }
                    }
                }
                stage('Unittest') {
                    steps {
                        script {
                            // Run unittests
                            bat 'python -m pytest --junitxml results.xml polybot/test'
                        }
                    }
                }
            }
        }
        stage('Security Vulnerability Scanning') {
            steps {
                script {
                    withCredentials([string(credentialsId: 'SNYK_API_TOKEN', variable: 'SNYK_TOKEN')]) {
                        // Scan the image
                        bat """
                            snyk auth $SNYK_TOKEN
                            snyk container test ${APP_IMAGE_NAME}:latest --severity-threshold=high || exit 0
                        """
                    }
                }
            }
        }
        stage('Login, Tag, and Push Images') {
            steps {
                script {
                    withCredentials([
                        usernamePassword(credentialsId: 'dockerhub', usernameVariable: 'USER', passwordVariable: 'PASS')
                    ]) {

                    // Login to Dockerhub, tag, and push images
                    bat """
                        cd polybot
                        docker login -u ${USER} -p ${PASS}
                        docker tag ${APP_IMAGE_NAME}:latest ${DOCKER_REPO}:${APP_IMAGE_NAME}-${env.IMAGE_TAG}
                        docker tag ${WEB_IMAGE_NAME}:latest ${DOCKER_REPO}:${WEB_IMAGE_NAME}-${env.IMAGE_TAG}
                        docker push ${DOCKER_REPO}:${APP_IMAGE_NAME}-${env.IMAGE_TAG}
                        docker push ${DOCKER_REPO}:${WEB_IMAGE_NAME}-${env.IMAGE_TAG}
                    """
                    }
                }
            }
        }
        stage('Deploy with Helm') {
            steps {
                script {
                    // Deploy the application using your Helm chart
                    bat """
                    helm upgrade --install python-app-0.1.0 ./my-python-app-chart \
                    --namespace demo \
                    --set image.repository=${DOCKER_REPO} \
                    --set image.tag=${env.IMAGE_TAG} \
                    """
                }
            }
        }
    }
}