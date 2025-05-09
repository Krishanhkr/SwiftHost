# Zero Trust Network Access (ZTNA) Implementation

## Overview

This implementation adds Zero Trust Network Access (ZTNA) security to the honeypot system. ZTNA is a security model that operates on the principle of "never trust, always verify" - treating all users and devices as potentially hostile until proven otherwise, regardless of whether they are inside or outside the network perimeter.

## Key Features

1. **Continuous Verification**
   - Device fingerprinting and trust scoring
   - Network context validation
   - Ongoing authentication checks for every request
   - User session monitoring and validation

2. **Least Privilege Access**
   - Role-based access control for all resources
   - Granular permissions based on user roles
   - Access policies enforced on every request
   - No implicit trust based on network location

3. **Encrypted Micro-Segmentation**
   - Logical separation of services and resources
   - Service mesh routing based on request properties
   - API gateways for controlled access to resources
   - Per-request authorization checks

4. **Token-Based Authentication**
   - JWT tokens with limited lifespan
   - Device binding for enhanced security
   - Role information embedded in tokens
   - Token revocation capabilities
   - Auto-refresh for continuous sessions

5. **Brute Force Protection**
   - Failed authentication tracking
   - Account lockout after multiple failed attempts
   - Gradual timeout increases
   - IP-based rate limiting

6. **Comprehensive Security Dashboards**
   - Real-time access monitoring
   - Device trust visualization
   - User session management
   - Policy configuration interface
   - Denial tracking and analysis

## Architecture

The ZTNA implementation consists of several components:

1. **Zero Trust Manager (`ZeroTrustManager` class)**
   - Core engine for implementing ZTNA policies
   - Handles request verification and processing
   - Maintains device fingerprints and trust scores
   - Logs access attempts and security events

2. **Authentication Blueprint (`auth_bp`)**
   - Provides authentication endpoints
   - Handles user login and token issuance
   - Manages token refresh and revocation
   - Provides access verification endpoints

3. **ZTNA Middleware**
   - Request processing pipeline that enforces ZTNA policies
   - Device verification
   - Network verification
   - Token validation
   - Authorization
   - Micro-segmentation

4. **Security Dashboards**
   - ZTNA status overview
   - Access logs and metrics
   - Policy management interface
   - Device management
   - User management

5. **Secure Login Interface**
   - Modern, secure login form
   - ZTNA-protected authentication flow
   - Role-based redirects after login
   - Client-side security features

## Role-Based Access Control

Access is controlled through the following roles:

| Role | Access Level |
|------|--------------|
| `admin` | Full access to all resources and administrative functions |
| `security_analyst` | Access to analytics dashboards and threat intelligence tools |
| `threat_hunter` | Access to deception technology controls and monitoring |
| Unauthenticated | Access to public resources only |

## Implementation Details

### Device Fingerprinting

The system creates and maintains fingerprints for all devices that connect to it:

```python
fingerprint_data = {
    'user_agent': request.headers.get('User-Agent', ''),
    'accept_language': request.headers.get('Accept-Language', ''),
    'accept_encoding': request.headers.get('Accept-Encoding', ''),
    'accept': request.headers.get('Accept', ''),
    'ip': request.remote_addr,
}
```

Each device is assigned a trust score (0.0-1.0) based on:
- Interaction frequency
- Behavioral patterns
- Suspicious activities
- User agent analysis

### Token-Based Authentication

Secure JWT tokens are used for authentication:

```python
payload = {
    'sub': user_data.get('id') or str(uuid.uuid4()),
    'username': user_data.get('username', 'anonymous'),
    'roles': user_data.get('roles', []),
    'fingerprint': user_data.get('fingerprint', ''),
    'iat': datetime.utcnow(),
    'exp': datetime.utcnow() + timedelta(seconds=expiry)
}
token = jwt.encode(payload, ZTNA_CONFIG['token_secret'], algorithm='HS256')
```

Tokens are delivered via secure, HTTP-only cookies to prevent JavaScript access and increase security against XSS attacks.

### Authorization Flow

For each request, the system performs the following checks:

1. Skip verification for static assets and public paths
2. Generate or retrieve device fingerprint
3. Calculate device trust score (if enabled)
4. Verify network context (IP restrictions)
5. Extract and validate authentication token
6. Check user roles against resource requirements
7. Apply service routing (micro-segmentation)
8. Log access attempt (success or failure)

## API Routes

### Authentication

- `POST /auth/login` - Authenticate user and issue token
- `POST /auth/logout` - Revoke current token
- `POST /auth/refresh-token` - Refresh an existing token
- `GET /auth/user` - Get current user information
- `POST /auth/check-access` - Check access to a specific resource

### ZTNA Administration

- `GET /admin/security/ztna` - ZTNA security dashboard
- `GET /admin/security/policies` - Policy management
- `GET /admin/security/devices` - Device management
- `GET /admin/security/users` - User management

## Configuration

ZTNA configuration is managed through environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `ZTNA_TOKEN_SECRET` | Secret key for JWT tokens | `honeypot_ztna_secret_key` |
| `ZTNA_TOKEN_EXPIRY` | Token expiry in seconds | `1800` (30 minutes) |
| `ZTNA_ALLOWED_NETWORKS` | Comma-separated list of allowed networks | Private networks |
| `ZTNA_HIGH_RISK_COUNTRIES` | Countries considered high risk | Empty |
| `ZTNA_ENFORCE_DEVICE` | Whether to enforce device verification | `false` |
| `ZTNA_SERVICE_MESH` | Whether to enable service mesh routing | `false` |
| `ZTNA_MAX_FAILED_ATTEMPTS` | Max failed login attempts | `5` |
| `ZTNA_LOCKOUT_DURATION` | Account lockout duration in seconds | `1800` |

## Usage

### Protecting Routes with ZTNA

```python
from security import ztna_login_required, ztna_role_required

@app.route('/admin/dashboard')
@ztna_login_required
@ztna_role_required(['admin'])
def admin_dashboard():
    return render_template('dashboard.html')
```

### Accessing User Information

```python
from flask import g

@app.route('/user-profile')
@ztna_login_required
def user_profile():
    user = g.user
    return render_template('profile.html', username=user.get('username'))
```

## Security Benefits

1. **Defense in Depth**: Multiple layers of security controls
2. **Reduced Attack Surface**: Least privilege minimizes exposure
3. **Insider Threat Protection**: All users verified regardless of origin
4. **Data Breach Mitigation**: Segmentation limits lateral movement
5. **Improved Visibility**: Comprehensive logging and monitoring
6. **Adaptive Security**: Dynamic trust scoring adjusts to behavior 