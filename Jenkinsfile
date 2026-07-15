#!/usr/bin/env groovy

/**
 * QIT 2.0 - Jenkins Pipeline
 *
 * This pipeline runs the AMQP Interoperability Test Suite across all supported
 * client shims (Python, JavaScript, C++, .NET, Java).
 *
 * Requirements:
 * - Docker (for broker)
 * - Python 3.11+
 * - uv (Python package manager)
 * - Node.js 18+ (for JavaScript shim)
 * - CMake + C++ compiler (for C++ shim)
 * - .NET SDK 8.0+ (for .NET shim)
 * - Java 11+ + Maven (for Java shim)
 */

pipeline {
    agent any

    options {
        // Keep last 30 builds
        buildDiscarder(logRotator(numToKeepStr: '30'))
        // Timeout after 30 minutes
        timeout(time: 30, unit: 'MINUTES')
        // Timestamps in console output
        timestamps()
        // ANSI color in console output
        ansiColor('xterm')
    }

    environment {
        // Python virtual environment
        VENV_DIR = '.venv'
        // Test results directory
        TEST_RESULTS_DIR = 'test-results'
        // Docker compose file for broker
        COMPOSE_FILE = 'docker/compose.yaml'
        // QIT version
        QIT_VERSION = '2.0.0'
    }

    stages {
        stage('Preparation') {
            steps {
                script {
                    echo "======================================"
                    echo "QIT ${QIT_VERSION} - Pipeline Started"
                    echo "======================================"
                    echo "Build: ${env.BUILD_NUMBER}"
                    echo "Job:   ${env.JOB_NAME}"
                    echo "Node:  ${env.NODE_NAME}"
                }

                // Clean previous test results
                sh "rm -rf ${TEST_RESULTS_DIR}"
                sh "mkdir -p ${TEST_RESULTS_DIR}"

                // Check prerequisites
                sh '''
                    echo "Checking prerequisites..."
                    python3 --version
                    uv --version || echo "WARNING: uv not found, will use pip"
                    docker --version
                    node --version || echo "WARNING: Node.js not found (JavaScript shim will be skipped)"
                    cmake --version || echo "WARNING: CMake not found (C++ shim will be skipped)"
                    dotnet --version || echo "WARNING: .NET SDK not found (.NET shim will be skipped)"
                    java -version || echo "WARNING: Java not found (Java shim will be skipped)"
                '''
            }
        }

        stage('Setup Python Environment') {
            steps {
                echo "Setting up Python environment..."
                sh '''
                    # Create virtual environment
                    if command -v uv &> /dev/null; then
                        uv venv
                        . ${VENV_DIR}/bin/activate
                        uv sync
                    else
                        python3 -m venv ${VENV_DIR}
                        . ${VENV_DIR}/bin/activate
                        pip install -e .
                    fi

                    # Verify installation
                    . ${VENV_DIR}/bin/activate
                    qit --version
                '''
            }
        }

        stage('Build Shims') {
            parallel {
                stage('Build JavaScript Shim') {
                    when {
                        expression {
                            return fileExists('shims/javascript-rhea/package.json')
                        }
                    }
                    steps {
                        echo "Building JavaScript/Rhea shim..."
                        dir('shims/javascript-rhea') {
                            sh '''
                                if command -v npm &> /dev/null; then
                                    npm install
                                    echo "✓ JavaScript shim ready"
                                else
                                    echo "⚠ Node.js not available, skipping JavaScript shim"
                                    exit 0
                                fi
                            '''
                        }
                    }
                }

                stage('Build C++ Shim') {
                    when {
                        expression {
                            return fileExists('shims/cpp-proton/CMakeLists.txt')
                        }
                    }
                    steps {
                        echo "Building C++ Proton shim..."
                        dir('shims/cpp-proton') {
                            sh '''
                                if command -v cmake &> /dev/null; then
                                    mkdir -p build
                                    cd build
                                    cmake ..
                                    make -j$(nproc)
                                    echo "✓ C++ shim ready"
                                else
                                    echo "⚠ CMake not available, skipping C++ shim"
                                    exit 0
                                fi
                            '''
                        }
                    }
                }

                stage('Build .NET Shim') {
                    when {
                        expression {
                            return fileExists('shims/dotnet-proton/QitShim.csproj')
                        }
                    }
                    steps {
                        echo "Building .NET Proton shim..."
                        dir('shims/dotnet-proton') {
                            sh '''
                                if command -v dotnet &> /dev/null; then
                                    dotnet restore
                                    dotnet build -c Release
                                    echo "✓ .NET shim ready"
                                else
                                    echo "⚠ .NET SDK not available, skipping .NET shim"
                                    exit 0
                                fi
                            '''
                        }
                    }
                }

                stage('Build Java Shim') {
                    when {
                        expression {
                            return fileExists('shims/java-protonj2/pom.xml')
                        }
                    }
                    steps {
                        echo "Building Java ProtonJ2 shim..."
                        dir('shims/java-protonj2') {
                            sh '''
                                if command -v mvn &> /dev/null; then
                                    mvn clean package -DskipTests
                                    echo "✓ Java shim ready"
                                else
                                    echo "⚠ Maven not available, skipping Java shim"
                                    exit 0
                                fi
                            '''
                        }
                    }
                }
            }
        }

        stage('Start Broker') {
            steps {
                echo "Starting Apache Artemis broker..."
                sh '''
                    # Stop any existing broker
                    docker compose -f ${COMPOSE_FILE} down || true

                    # Start broker
                    docker compose -f ${COMPOSE_FILE} up -d

                    # Wait for broker to be ready
                    echo "Waiting for broker to be ready..."
                    sleep 10

                    # Verify broker is running
                    docker compose -f ${COMPOSE_FILE} ps

                    echo "✓ Broker ready"
                '''
            }
        }

        stage('Run Tests') {
            steps {
                echo "Running QIT 2.0 test suite..."
                sh '''
                    . ${VENV_DIR}/bin/activate

                    # Run full test matrix with JUnit XML output
                    qit test amqp-types \\
                        --broker amqp://localhost:5672 \\
                        --junit-xml ${TEST_RESULTS_DIR}/qit-results.xml \\
                        || EXIT_CODE=$?

                    # Exit with test result code
                    exit ${EXIT_CODE:-0}
                '''
            }
        }
    }

    post {
        always {
            // Publish JUnit test results
            junit testResults: "${TEST_RESULTS_DIR}/*.xml", allowEmptyResults: true

            // Archive test artifacts
            archiveArtifacts artifacts: "${TEST_RESULTS_DIR}/**/*", allowEmptyArchive: true

            // Stop broker
            sh '''
                echo "Stopping broker..."
                docker compose -f ${COMPOSE_FILE} down || true
            '''

            // Cleanup
            sh '''
                echo "Cleaning up Docker resources..."
                docker system prune -f --volumes || true
            '''
        }

        success {
            echo "✓ QIT 2.0 Tests PASSED!"
        }

        failure {
            echo "✗ QIT 2.0 Tests FAILED"
        }

        unstable {
            echo "⚠ QIT 2.0 Tests UNSTABLE"
        }
    }
}
