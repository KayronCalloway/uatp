# CI/CD Pipeline Guide

## Overview

The UATP Capsule Engine uses GitHub Actions for continuous integration and deployment. This guide outlines the CI/CD pipeline structure and workflows.

## Workflows

### 1. Test Suite (`test.yml`)
**Triggers:** Push to main/develop, PRs to main/develop

**Services:**
- PostgreSQL 13
- Redis 6

**Steps:**
1. Set up Python 3.9 environment
2. Install dependencies with caching
3. Set up test database and Redis
4. Run database migrations
5. Execute unit tests with coverage
6. Run integration tests
7. Upload coverage reports to Codecov
8. Save test artifacts

### 2. Code Quality (`code-quality.yml`)
**Triggers:** Push to main/develop, PRs to main/develop

**Checks:**
- **Linting:** Black formatting, isort import sorting, flake8 linting
- **Type Checking:** mypy static type analysis
- **Complexity:** radon complexity analysis, xenon cyclomatic complexity
- **Documentation:** pydocstyle docstring quality
- **Security:** pip-audit dependency vulnerability scan

### 3. Security Scans (`security.yml`)
**Triggers:** Push to main/develop, PRs to main/develop, daily schedule

**Scans:**
- **Bandit:** Python security linter
- **Safety:** Dependency vulnerability scanner
- **Gitleaks:** Secret detection
- **Trivy:** Filesystem vulnerability scanner

### 4. Performance Testing (`performance.yml`)
**Triggers:** Push to main, PRs to main, weekly schedule

**Tests:**
- Performance benchmarks
- Load testing with custom framework
- Locust-based load testing
- Performance regression detection

### 5. Build and Deploy (`build.yml`)
**Triggers:** Push to main, version tags

**Steps:**
1. Build Docker image with BuildKit
2. Push to Docker Hub with proper tags
3. Deploy to staging (on main branch)
4. Deploy to production (on version tags)

### 6. Release (`release.yml`)
**Triggers:** Version tags (v*)

**Steps:**
1. Create GitHub release with notes
2. Build and push Docker images with version tags
3. Deploy to production environment
4. Send deployment notifications

## Setup Instructions

### 1. Repository Secrets

Configure these secrets in your GitHub repository:

```bash
# Docker Hub
DOCKER_USERNAME=your_docker_username
DOCKER_PASSWORD=your_docker_password

# Slack notifications (optional)
SLACK_WEBHOOK_URL=your_slack_webhook_url

# Production deployment (optional)
PROD_DEPLOY_KEY=your_production_deployment_key
```

### 2. Environment Variables

Create `.env.example` file with required variables:

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/uatp
REDIS_URL=redis://localhost:6379

# API Keys (for testing)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 3. Database Setup

The CI pipeline automatically:
- Spins up PostgreSQL and Redis containers
- Runs Alembic migrations
- Prepares test database

### 4. Coverage Reporting

Integration with Codecov:
- Upload coverage reports automatically
- Fail CI if coverage drops below threshold
- Generate HTML coverage reports

## Local Development

### Running Tests Locally

```bash
# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov

# Run tests with coverage
pytest tests/ -v --cov=src --cov-report=html

# Run specific test types
pytest tests/test_integration.py -v
pytest tests/ -k "security" -v
```

### Code Quality Checks

```bash
# Install tools
pip install black isort flake8 mypy bandit safety

# Format code
black src/
isort src/

# Check linting
flake8 src/ --max-line-length=88 --extend-ignore=E203,W503

# Type checking
mypy src/ --ignore-missing-imports

# Security scanning
bandit -r src/
safety check
```

### Performance Testing

```bash
# Run performance benchmarks
python src/testing/performance_benchmarks.py

# Run load tests
python src/testing/load_testing.py

# Run Locust load test
locust -f locustfile.py --host=http://localhost:8000
```

## Deployment Pipeline

### Staging Deployment
- Triggered on every push to `main`
- Deploys latest Docker image
- Runs smoke tests
- Notifies team of deployment status

### Production Deployment
- Triggered on version tags (`v1.0.0`, `v1.1.0`, etc.)
- Creates GitHub release
- Builds production Docker image
- Deploys to production environment
- Sends deployment notifications

### Rollback Strategy
- Keep last 5 Docker images for quick rollback
- Database migration rollback scripts
- Blue-green deployment for zero-downtime updates

## Monitoring and Alerts

### CI/CD Metrics
- Build success rate
- Test execution time
- Deployment frequency
- Mean time to recovery

### Performance Regression Detection
- Automated performance baseline comparison
- Alert on significant performance degradation
- Historical performance trend analysis

### Security Monitoring
- Daily vulnerability scans
- Dependency update alerts
- Secret detection in commits

## Best Practices

### Pull Request Workflow
1. Create feature branch from `develop`
2. Implement changes with tests
3. Run local quality checks
4. Submit PR with proper description
5. Address CI feedback
6. Merge after approval

### Release Process
1. Create release branch from `develop`
2. Update version numbers
3. Update CHANGELOG.md
4. Merge to `main`
5. Create version tag
6. Monitor deployment

### Security Guidelines
- Never commit secrets or API keys
- Use environment variables for configuration
- Regularly update dependencies
- Monitor security scan results

## Troubleshooting

### Common CI Issues

**Tests failing in CI but passing locally:**
- Check environment differences
- Verify database setup
- Check async test isolation

**Docker build failures:**
- Check Dockerfile syntax
- Verify base image availability
- Check file permissions

**Performance test failures:**
- Check resource limits
- Verify database performance
- Monitor system resources

### Getting Help
- Check GitHub Actions logs
- Review error messages carefully
- Consult team documentation
- Ask for help in team channels

## Configuration Files

### Key CI Configuration Files
- `.github/workflows/` - All GitHub Actions workflows
- `.github/PULL_REQUEST_TEMPLATE.md` - PR template
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container build instructions
- `docker-compose.yml` - Local development setup
- `pytest.ini` - Test configuration
- `.gitleaks.toml` - Secret detection configuration

This CI/CD pipeline ensures code quality, security, and performance while enabling rapid and reliable deployments.
