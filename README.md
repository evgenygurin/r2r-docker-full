# R2R Docker Full

[![Security Scan](https://github.com/evgenygurin/r2r-docker-full/actions/workflows/security-scan.yml/badge.svg)](https://github.com/evgenygurin/r2r-docker-full/actions/workflows/security-scan.yml)
[![Docker Build](https://github.com/evgenygurin/r2r-docker-full/actions/workflows/docker-build.yml/badge.svg)](https://github.com/evgenygurin/r2r-docker-full/actions/workflows/docker-build.yml)
[![Lint](https://github.com/evgenygurin/r2r-docker-full/actions/workflows/lint.yml/badge.svg)](https://github.com/evgenygurin/r2r-docker-full/actions/workflows/lint.yml)
[![Release](https://github.com/evgenygurin/r2r-docker-full/actions/workflows/release.yml/badge.svg)](https://github.com/evgenygurin/r2r-docker-full/actions/workflows/release.yml)

Production-ready R2R (RAG to Riches) deployment with Docker Compose.

## Quick Start

```bash
# Start R2R stack
docker compose -f compose.full.yaml --profile postgres --profile minio up -d

# Wait for services to start
sleep 45

# Check health
curl http://localhost:7272/v3/health
```

## Documentation

- **Configuration**: See `CLAUDE.md` for comprehensive project documentation
- **Workflows**: See `docs/workflows.md` for CI/CD information
- **Deployment**: See `.claude/rules/deployment.md` for deployment procedures

## Features

- Full R2R stack with PostgreSQL, MinIO, and Unstructured
- Automated CI/CD with GitHub Actions
- Security scanning and validation
- Production deployment to GCP

## Requirements

- Docker and Docker Compose
- Python 3.11+ (for local development)
- GCP account (for production deployment)

## Support

For issues and questions, see the project documentation in `CLAUDE.md` and `.claude/rules/`.
