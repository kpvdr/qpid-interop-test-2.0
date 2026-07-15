# QIT 2.0 - CI/CD Setup Guide

## Overview

QIT 2.0 includes a complete Jenkins pipeline for automated testing of AMQP interoperability across all supported client shims.

**Pipeline Features:**
- ✅ Automated shim builds (C++, .NET, Java, JavaScript)
- ✅ Dockerized broker management (Apache Artemis)
- ✅ Full test matrix execution (450 tests across 5 shims)
- ✅ JUnit XML reporting
- ✅ Test result trending and analysis
- ✅ Parallel shim builds
- ✅ Automatic cleanup

## Jenkins Pipeline

### Location
- **Jenkinsfile**: `./Jenkinsfile`
- **Pipeline Type**: Declarative Pipeline
- **Estimated Duration**: 10-15 minutes

### Pipeline Stages

1. **Preparation** (~10 seconds)
   - Checks prerequisites (Python, Docker, build tools)
   - Creates test results directory
   - Displays environment info

2. **Setup Python Environment** (~20 seconds)
   - Creates virtual environment with `uv`
   - Installs QIT framework and dependencies
   - Verifies installation

3. **Build Shims** (~30-60 seconds, parallel)
   - **JavaScript**: `npm install`
   - **C++**: `cmake + make`
   - **.NET**: `dotnet build`
   - **Java**: `mvn package`
   - Builds run in parallel for speed
   - Gracefully skips missing build tools

4. **Start Broker** (~15 seconds)
   - Stops any existing broker
   - Starts Apache Artemis via Docker Compose
   - Waits for broker readiness
   - Verifies broker is healthy

5. **Run Tests** (~10 minutes)
   - Executes full 450-test matrix
   - Generates JUnit XML report
   - Captures detailed failure information

6. **Post Actions** (always runs)
   - Publishes JUnit test results to Jenkins
   - Archives test artifacts
   - Stops broker
   - Cleans up Docker resources

### Jenkins Configuration

#### Create the Pipeline Job

1. **In Jenkins UI:**
   - New Item → Pipeline
   - Name: `QIT-2.0-Tests`
   - Pipeline definition: Pipeline script from SCM

2. **Configure SCM:**
   - SCM: Git
   - Repository URL: `<your-git-repo-url>`
   - Branch: `*/main` (or your branch)
   - Script Path: `Jenkinsfile`

3. **Build Triggers:**
   - Poll SCM: `H/15 * * * *` (check every 15 minutes)
   - Or webhook trigger on push

4. **Build Parameters** (optional):
   ```
   String: SENDER_SHIMS (default: all)
   String: RECEIVER_SHIMS (default: all)
   String: AMQP_TYPES (default: all)
   ```

#### Required Plugins
- **Pipeline**: Core pipeline support
- **JUnit**: Test result publishing
- **AnsiColor**: Color console output
- **Timestamper**: Timestamps in logs
- **Docker Pipeline**: Docker support (if needed)

### Node Requirements

The Jenkins agent/node must have:

#### Required
- **Docker**: For broker management
- **Python 3.11+**: Framework runtime
- **uv** (or pip): Python package management

#### Optional (for full coverage)
- **Node.js 18+**: JavaScript shim
- **CMake + C++ compiler**: C++ shim
- **.NET SDK 8.0+**: .NET shim
- **Java 11+ + Maven**: Java shim

**Note**: The pipeline gracefully skips shims if build tools are missing.

### Setup Node with All Tools

```bash
# Fedora/RHEL
sudo dnf install -y \
    python3.11 \
    docker \
    nodejs \
    cmake \
    gcc-c++ \
    dotnet-sdk-8.0 \
    java-11-openjdk-devel \
    maven

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Enable Docker
sudo systemctl enable --now docker
sudo usermod -aG docker jenkins
```

## JUnit XML Output

### Command-Line Usage

```bash
# Generate JUnit XML report
qit test amqp-types --junit-xml test-results.xml

# With specific shims
qit test amqp-types \
    --sender python-proton cpp-proton \
    --receiver python-proton cpp-proton \
    --junit-xml test-results.xml
```

### XML Format

The JUnit XML report includes:
- **Test Suite**: QIT AMQP Interoperability Tests
- **Test Cases**: One per sender/receiver/type combination
- **Class Name**: `qit.{sender}.{receiver}`
- **Test Name**: `{amqp_type}`
- **Time**: Duration in seconds
- **Failures**: Detailed diff information

Example:
```xml
<testsuite name="QIT AMQP Interoperability Tests" tests="450" failures="89" errors="0">
  <testcase classname="qit.python-proton.cpp-proton" name="int" time="0.052"/>
  <testcase classname="qit.python-proton.javascript-rhea" name="long" time="0.048">
    <failure message="4 message difference(s)" type="InteroperabilityFailure">
      Error: 64-bit integer overflow
      Message Differences (4 total):
        - Message 0: value mismatch for type long
        - Message 3: value mismatch for type long
    </failure>
  </testcase>
</testsuite>
```

### Jenkins Integration

Jenkins automatically:
- Parses JUnit XML files
- Displays pass/fail trends over builds
- Shows test duration graphs
- Provides drill-down into failures
- Tracks flaky tests

## Advanced Configuration

### Environment Variables

Set in Jenkins job configuration or `Jenkinsfile`:

```groovy
environment {
    // Override broker URL
    BROKER_URL = 'amqp://artemis.example.com:5672'
    
    // Test subset
    SENDER_SHIMS = 'python-proton,cpp-proton'
    RECEIVER_SHIMS = 'python-proton,cpp-proton'
    AMQP_TYPES = 'int,string,binary'
    
    // Timeout
    TEST_TIMEOUT = '20'  // minutes
}
```

### Parameterized Builds

Add parameters to the pipeline:

```groovy
parameters {
    choice(
        name: 'TEST_SCOPE',
        choices: ['full', 'smoke', 'regression'],
        description: 'Test scope to run'
    )
    booleanParam(
        name: 'SKIP_BROKER_CLEANUP',
        defaultValue: false,
        description: 'Keep broker running after tests'
    )
}
```

### Parallel Testing

For faster execution, split tests by shim or type:

```groovy
stage('Run Tests') {
    parallel {
        stage('Test Python') {
            steps {
                sh 'qit test amqp-types --sender python-proton --receiver python-proton'
            }
        }
        stage('Test C++') {
            steps {
                sh 'qit test amqp-types --sender cpp-proton --receiver cpp-proton'
            }
        }
        // etc.
    }
}
```

### Notifications

Add Slack/email notifications:

```groovy
post {
    failure {
        mail to: 'team@example.com',
             subject: "QIT 2.0 Tests Failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
             body: "Check console output at ${env.BUILD_URL}"
    }
}
```

## Monitoring and Debugging

### View Test Results

**Jenkins UI:**
1. Build → Test Results
2. See pass/fail by test case
3. Drill down to failure details
4. View trends across builds

**Console Output:**
- Full test execution log
- Shim build output
- Broker startup logs
- Test failure details

### Common Issues

#### 1. Broker Won't Start
```
Error: docker compose up failed
```
**Solution**: Check Docker daemon is running, ports aren't in use
```bash
sudo systemctl start docker
docker ps  # check for port 5672 conflicts
```

#### 2. Shim Build Fails
```
Error: cmake: command not found
```
**Solution**: Install missing build tools or update Jenkinsfile to skip
```bash
sudo dnf install cmake gcc-c++
```

#### 3. Tests Timeout
```
Error: Receive failed: timeout
```
**Solution**: Increase timeout, check broker health
```bash
docker logs qit-artemis  # check broker logs
```

#### 4. Permission Denied
```
Error: Got permission denied while trying to connect to Docker
```
**Solution**: Add jenkins user to docker group
```bash
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
```

## Performance Optimization

### Reduce Test Time

1. **Run subset for quick feedback:**
   ```bash
   qit test amqp-types --type int,string,boolean
   ```

2. **Test only modified shims:**
   ```bash
   qit test amqp-types --sender python-proton --receiver python-proton
   ```

3. **Use test result caching:**
   - Jenkins caches Docker images
   - Reuse Python virtual environment
   - Skip clean builds when possible

### Resource Optimization

- **CPU**: Parallel shim builds use all cores
- **Memory**: ~2GB for full test suite
- **Disk**: ~500MB for Docker images + artifacts
- **Network**: Local broker (no external dependencies)

## Comparison: Old vs New Pipeline

| Feature | QIT 1.0 | QIT 2.0 |
|---------|---------|---------|
| **Test Count** | ~50 | 450 |
| **Languages** | 2-3 | 5 |
| **Duration** | 15 min | 10-15 min |
| **Reporting** | Basic | JUnit XML + Trends |
| **Broker** | Manual | Automated (Docker) |
| **Shim Builds** | Manual | Automated + Parallel |
| **Failure Details** | Limited | Comprehensive diffs |
| **CI/CD Ready** | Partial | Complete |

## Next Steps

1. **Set up Jenkins job** using instructions above
2. **Run first build** to verify setup
3. **Review test results** and establish baseline
4. **Configure notifications** for failures
5. **Add to PR workflow** for regression testing

## Support

For issues or questions:
- Check Jenkins console output
- Review `test-results/qit-results.xml`
- Check broker logs: `docker logs qit-artemis`
- See `README.md` for QIT framework details

---

**Status**: ✅ Production Ready  
**Last Updated**: 2026-07-15
