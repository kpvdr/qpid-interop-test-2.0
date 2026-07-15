# Jenkins Configuration for QIT 2.0

## Quick Setup

### 1. Create Jenkins Job

1. Go to Jenkins → New Item
2. Name: `QIT-2.0-Tests`
3. Type: Pipeline
4. Click OK

### 2. Configure Pipeline

**Pipeline Section:**
- Definition: Pipeline script from SCM
- SCM: Git
- Repository URL: `<your-repo-url>`
- Branch Specifier: `*/main`
- Script Path: `Jenkinsfile`

**Build Triggers:**
- ☑ Poll SCM: `H/15 * * * *` (every 15 minutes)
- Or configure webhook for instant triggers

**Save**

### 3. Prepare Jenkins Node

The node needs these tools installed:

```bash
# Required
sudo dnf install -y python3.11 docker

# Python package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Optional (for all shims)
sudo dnf install -y nodejs cmake gcc-c++ dotnet-sdk-8.0 java-11-openjdk-devel maven

# Enable Docker
sudo systemctl enable --now docker
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
```

### 4. Run First Build

1. Go to job page
2. Click "Build Now"
3. Watch console output
4. Check test results after completion

## Pipeline Overview

```
Preparation (10s)
  ↓
Setup Python (20s)
  ↓
Build Shims - Parallel (60s)
├─ JavaScript (npm install)
├─ C++ (cmake + make)
├─ .NET (dotnet build)
└─ Java (mvn package)
  ↓
Start Broker (15s)
  ↓
Run Tests (10 min)
  ↓
Publish Results & Cleanup
```

**Total Duration**: ~12-15 minutes

## Viewing Results

### Test Results Tab
- Click on build → Test Results
- See 450 test cases organized by shim pairs
- Drill down into failures
- View trends across builds

### Console Output
- Full execution log
- Build output from each shim
- Test execution details
- Failure information

### Artifacts
- `test-results/qit-results.xml` - JUnit XML report
- Preserved for 30 builds

## Customization

### Run Subset of Tests

Edit the "Run Tests" stage in Jenkinsfile:

```groovy
// Test only Python and C++
qit test amqp-types \
    --sender python-proton cpp-proton \
    --receiver python-proton cpp-proton \
    --junit-xml ${TEST_RESULTS_DIR}/qit-results.xml
```

### Add Parameters

Add to Jenkinsfile before stages:

```groovy
parameters {
    choice(
        name: 'TEST_SCOPE',
        choices: ['full', 'smoke'],
        description: 'Which tests to run'
    )
}
```

Use in stage:
```groovy
script {
    if (params.TEST_SCOPE == 'smoke') {
        sh 'qit test amqp-types --type int string boolean'
    } else {
        sh 'qit test amqp-types'
    }
}
```

### Notifications

Add to `post` section:

```groovy
post {
    failure {
        emailext(
            subject: "QIT Tests Failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
            body: "Check ${env.BUILD_URL}",
            to: 'team@example.com'
        )
    }
}
```

## Troubleshooting

### Build Fails Immediately
- Check node has required tools
- Verify Docker is running and jenkins user is in docker group

### Shim Builds Fail
- Check console output for specific errors
- Verify build tools are installed
- Pipeline gracefully skips missing tools

### Tests Timeout
- Check broker is healthy: `docker logs qit-artemis`
- Increase timeout in Jenkinsfile
- Run subset of tests

### No Test Results
- Check `test-results/*.xml` was created
- Verify JUnit plugin is installed
- Check console for XML generation errors

## Monitoring

### Health Checks
- Pass rate should stay ~80%
- Duration should stay ~10-15 minutes
- Watch for flaky tests in trends

### When to Investigate
- Pass rate drops below 75%
- Duration increases significantly
- New failures appear consistently

## Next Steps

1. ✅ Create and configure job
2. ✅ Run successful build
3. Set up notifications
4. Add to PR workflow
5. Monitor trends

See [CI_CD_SETUP.md](../CI_CD_SETUP.md) for complete documentation.
