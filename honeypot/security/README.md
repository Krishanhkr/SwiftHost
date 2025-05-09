# Zero Trust Network Access (ZTNA) Security Module

The ZTNA security module implements a comprehensive zero trust security model for the honeypot system, providing continuous verification, least privilege access, and micro-segmentation.

## Core Principles

This module follows the key principles of Zero Trust architecture:

1. **Never Trust, Always Verify**: Every request is verified regardless of origin
2. **Least Privilege Access**: Users only have access to resources they specifically need
3. **Assume Breach**: All traffic is treated as potentially malicious
4. **Continuous Verification**: Authentication and authorization happen for every request
5. **Micro-segmentation**: Network is segmented into secure zones

## Components

### Zero Trust Manager (`zero_trust.py`)

The core ZTNA engine that handles:

- Device fingerprinting and trust evaluation
- Network context verification
- Token-based continuous authentication
- Role-based access control
- Service routing (micro-segmentation)
- Security event logging

### Authentication Routes (`auth_routes.py`)

Provides API endpoints for:

- User authentication and token issuance
- Token refresh and revocation
- User information retrieval
- Access control verification

### Secure Login UI (`templates/secure_login.html`)

A modern, secure login interface that integrates with the ZTNA system.

## Implementation Details

### Device Fingerprinting

Each device connecting to the system is fingerprinted based on multiple attributes:
- User agent string
- Accept headers
- IP address
- Other browser characteristics

A trust score is calculated for each device based on its behavior and characteristics.

### Token-Based Authentication

The system uses JWT (JSON Web Tokens) for authentication with:
- Limited token lifespan
- Device binding
- Role embedding
- Auto-refresh for continuous sessions
- Token revocation capabilities

### Role-Based Access Control

Access to resources is controlled by roles:
- `admin`: Full system access
- `security_analyst`: Access to analytics and threat intelligence
- `threat_hunter`: Access to deception technology and honeypot management
- Default user: Limited to public resources

### Micro-segmentation

Requests are routed through appropriate service paths based on the resource being accessed:
- Admin portal → Admin service
- Analytics → Analytics service
- Deception tech → Deception service
- API → API gateway

### Brute Force Protection

The system includes protection against brute force attacks:
- Failed authentication tracking
- Account lockout after multiple failed attempts
- Gradual timeout increases

## Integration

To integrate ZTNA with the honeypot application:

1. Initialize the ZTNA manager:
   ```python
   from security import ztna_manager
   ztna_manager.init_app(app)
   ```

2. Register authentication routes:
   ```python
   from security import auth_bp
   app.register_blueprint(auth_bp, url_prefix='/auth')
   ```

3. Apply ZTNA decorators to protected routes:
   ```python
   from security import ztna_login_required, ztna_role_required
   
   @app.route('/admin/dashboard')
   @ztna_login_required
   @ztna_role_required(['admin'])
   def admin_dashboard():
       return render_template('admin/dashboard.html')
   ```

## Configuration

Configuration options are loaded from environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `ZTNA_TOKEN_SECRET` | Secret key for JWT tokens | `honeypot_ztna_secret_key` |
| `ZTNA_TOKEN_EXPIRY` | Token expiry in seconds | `1800` (30 minutes) |
| `ZTNA_ALLOWED_NETWORKS` | Comma-separated list of allowed networks | `10.0.0.0/8,172.16.0.0/12,192.168.0.0/16` |
| `ZTNA_ENFORCE_DEVICE` | Whether to enforce device verification | `false` |
| `ZTNA_SERVICE_MESH` | Whether to enable service mesh routing | `false` |
| `ZTNA_MAX_FAILED_ATTEMPTS` | Max failed login attempts before lockout | `5` |
| `ZTNA_LOCKOUT_DURATION` | Account lockout duration in seconds | `1800` (30 minutes) | 