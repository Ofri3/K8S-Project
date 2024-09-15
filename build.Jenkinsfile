pipeline {
    agent {
        kubernetes {
            yaml """
            apiVersion: v1
            kind: Pod
            spec:
              serviceAccountName: jenkins  # Ensure Jenkins is using the correct service account
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
        APP_IMAGE_NAME = 'app-image'
        WEB_IMAGE_NAME = 'web-image'
        DOCKER_COMPOSE_FILE = 'compose.yaml'
        DOCKER_REPO = 'ofriz/k8sproject'
        DOCKERHUB_CREDENTIALS = 'dockerhub'
        CHART_VERSION = "0.1.${BUILD_NUMBER}"
        KUBECONFIG = "${env.WORKSPACE}/.kube/config"
    }

    stages {
        stage('Install Python Requirements') {
            steps {
                container('jenkins-agent') {
                    // Install Python dependencies
                    sh """
                        python3 -m venv venv
                        . venv/bin/activate
                        pip install pytest unittest2 pylint flask telebot Pillow loguru matplotlib
                    """
                }
            }
        }
        stage('Unittest') {
            steps {
                container('jenkins-agent') {
                    // Run unittests
                    sh """
                        python3 -m venv venv
                        . venv/bin/activate
                        python -m pytest --junitxml results.xml polybot/test
                    """
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
                            helm package ./my-python-app-chart
                        """
                    }
                }
            }
        }
        stage('Deploy with Helm') {
            steps {
                container('jenkins-agent') {
                    script {
                        withEnv(["KUBECONFIG=${env.KUBECONFIG}"]) {
                            def CHART_VERSION = "${env.CHART_VERSION}"  // auto-increment based on build number
                            sh """
                                helm upgrade --install my-python-app ./my-python-app-${CHART_VERSION}.tgz \
                                --atomic --wait \
                                --namespace jenkins \
                            """
                        }
                    }
                }
            }
        }
        stage('Create/Update ArgoCD Application') {
            steps {
                container('jenkins-agent') {
                    script {
                        // Make sure 'app.yaml' is in the 'argocd-config' folder
                        sh 'kubectl apply -f argocd-config/app.yaml -n argocd'
                    }
                }
            }
        }
        stage('Sync ArgoCD Application') {
            steps {
                container('jenkins-agent') {
                    script {
                        sh 'kubectl -n argocd patch application my-python-app --type merge -p \'{"metadata": {"annotations": {"argocd.argoproj.io/sync-wave": "-1"}}}\''
                    }
                }
            }
        }
    }
}