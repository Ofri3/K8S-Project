pipeline {
    agent {
        kubernetes {
            yaml """
            apiVersion: v1
            kind: Pod
            spec:
              containers:
              - name: jenkins-agent
                image: ofriz/k8sproject:jenkins-agent-latest
                securityContext:
                  privileged: true       # Enable privileged mode for Docker
                  runAsUser: 0           # Run as root user to access Docker socket
                command:
                - sh
                - -c
                - |
                  git config --global --add safe.directory /home/jenkins/agent/workspace/kubernetes-project-pipeline
                  cat
                tty: true
                volumeMounts:
                - mountPath: /var/run/docker.sock
                  name: docker-sock
                - mountPath: /home/jenkins/agent
                  name: workspace-volume
              volumes:
              - hostPath:
                  path: /var/run/docker.sock
                name: docker-sock
              - emptyDir:
                  medium: ""
                name: workspace-volume
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
        stage('Extract Git Commit Hash') {
            steps {
                // Extract Git commit hash
                script {
                    sh(script: 'git rev-parse --short HEAD > gitCommit.txt')
                    def GITCOMMIT = readFile('gitCommit.txt').trim()
                    env.GIT_TAG = "${GITCOMMIT}"

                    // Set IMAGE_TAG as an environment variable
                    env.IMAGE_TAG = "v1.0.0-${BUILD_NUMBER}-${GIT_TAG}"
                }
            }
        }
        stage('Build Docker Image') {
            steps {
                container('jenkins-agent') {
                    script {
                        withCredentials([usernamePassword(credentialsId: 'dockerhub', usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                            echo "Checking Docker installation"
                            sh 'docker --version || echo "Docker command failed"'
                            // Ensure Docker commands run in the jenkins-agent container
                            // Build Docker image using docker-compose
                            sh """
                                docker-compose -f ${DOCKER_COMPOSE_FILE} build
                            """
                        }
                    }
                }
            }
        }
        stage('Install Python Requirements') {
            steps {
                // Install Python dependencies
                sh """
                    pip install --upgrade pip
                    pip install pytest unittest2 pylint flask telebot Pillow loguru matplotlib
                """
            }
        }
        stage('Static Code Linting and Unittest') {
            parallel {
                stage('Static code linting') {
                    steps {
                        // Run python code analysis
                        sh """
                            python -m pylint -f parseable --reports=no polybot/*.py > pylint.log
                            cat pylint.log
                        """
                    }
                }
                stage('Unittest') {
                    steps {
                        // Run unittests
                        sh 'python -m pytest --junitxml results.xml polybot/test'
                    }
                }
            }
        }
        stage('Security Vulnerability Scanning') {
            steps {
                script {
                    withCredentials([string(credentialsId: 'SNYK_API_TOKEN', variable: 'SNYK_TOKEN')]) {
                        // Scan the image
                        sh """
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
                    sh """
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
                // Deploy the application using your Helm chart
                sh """
                    helm upgrade --install python-app-0.1.0 ./my-python-app-chart \
                    --namespace demo \
                    --set image.repository=${DOCKER_REPO} \
                    --set image.tag=${env.IMAGE_TAG} \
                    """
            }
        }
    }
}