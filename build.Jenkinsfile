pipeline {
    agent {
        kubernetes {
            yaml """
            apiVersion: v1
            kind: Pod
            spec:
              serviceAccountName: jenkins-admin  # Ensure Jenkins is using the correct service account
              containers:
              - name: jenkins-agent
                image: ofriz/k8sproject:jenkins-agent-1.1
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
        CHART_VERSION = "0.1.${BUILD_NUMBER}"
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
                            sh 'docker-compose -f ${DOCKER_COMPOSE_FILE} build'
                        }
                    }
                }
            }
        }
        stage('Login, Tag, and Push Images') {
            steps {
                container('jenkins-agent') {
                    script {
                        withCredentials([usernamePassword(credentialsId: 'dockerhub', usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                        // Login to Dockerhub, tag, and push images
                        sh """
                            cd polybot
                            docker login -u ${USER} -p ${PASS}
                            docker tag ${APP_IMAGE_NAME}:latest ${DOCKER_REPO}:${APP_IMAGE_NAME}-latest
                            docker tag ${WEB_IMAGE_NAME}:latest ${DOCKER_REPO}:${WEB_IMAGE_NAME}-latest
                            docker push ${DOCKER_REPO}:${APP_IMAGE_NAME}-latest
                            docker push ${DOCKER_REPO}:${WEB_IMAGE_NAME}-latest
                        """
                        }
                    }
                }
            }
        }
        stage('Package Helm Chart') {
            steps {
                container('jenkins-agent') {
                    script {
                        // Update the chart version in Chart.yaml and package the chart
                        sh """
                            sed -i 's/^version:.*/version: ${CHART_VERSION}/' my-python-app-chart/Chart.yaml
                            helm package ./my-python-app-chart --version ${CHART_VERSION}
                        """
                    }
                }
            }
        }
        stage('Deploy with Helm') {
            steps {
                container('jenkins-agent') {
                    script {
                        def CHART_VERSION = "${env.CHART_VERSION}"  // auto-increment based on build number
                        sh """
                            helm upgrade --install my-python-app-${CHART_VERSION} ./my-python-app-chart-${CHART_VERSION}.tgz \
                            --namespace demo \
                        """
                    }
                }
            }
        }
    }
}