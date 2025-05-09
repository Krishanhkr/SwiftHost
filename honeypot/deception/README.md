# Deception Technology Module

This module implements fake microservices mimicking Redis, MySQL, and AWS S3 APIs that log attacker behavior and inject tracking payloads.

## Overview

The deception technology module creates realistic-looking API endpoints that appear to expose sensitive configuration data and credentials. In reality, these endpoints are honeypots designed to:

1. Track attacker behavior and techniques
2. Inject tracking payloads that can be detected if used later
3. Identify potential data exfiltration patterns
4. Profile attackers based on their interaction patterns

## Components

### API Honeypot (`api_honeypot.py`)

Implements fake API endpoints mimicking:
- Redis configuration and authentication endpoints
- MySQL connection information and database backup endpoints
- AWS S3 configuration, listing, and download endpoints

Each endpoint injects invisible tracking payloads into the responses that can be detected if an attacker uses the stolen credentials.

### Analytics (`analytics.py`)

Provides advanced analytics capabilities:
- Attacker behavior profiling based on interaction patterns
- Sophistication scoring of attackers
- Tracking of credential payload usage
- Detection of data exfiltration patterns

## Integration

The module is integrated with the main honeypot application:
- Registers API endpoints under the `/services` URL prefix
- Monitors all incoming requests for tracking payload usage
- Provides a dedicated analytics dashboard at `/admin/deception-analytics`
- Integrates with the blockchain evidence logging system

## Usage

Access the deception endpoints at:
- `/services/redis/config` - Fake Redis configuration
- `/services/mysql/connection` - Fake MySQL connection details
- `/services/aws/s3/config` - Fake AWS S3 credentials
- `/services/admin/interactions` - View recorded interactions

View the analytics dashboard at:
- `/admin/deception-analytics`

## Security Notes

- The fake credentials should be rotated regularly to avoid detection
- In a production environment, these endpoints should be properly secured to prevent false positives
- Real credentials should NEVER be used, even as placeholders 