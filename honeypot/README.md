# AI-Powered Honeypot with Fake Data Generation

This project implements an advanced honeypot system with AI-generated fake data to lure and analyze attacker behavior.

## Features

### 1. AI-Powered Fake Data Generation
- **Text Data**: Generates convincing fake user data, credentials, and financial transactions
- **Image Data**: Simulates deepfake profile images (mock implementation)
- **Variety and Realism**: Built-in inconsistencies and patterns that mimic real systems

### 2. Deceptive API Endpoints
- Simulated user authentication system
- Fake administrative interfaces
- Deliberately exposed "sensitive" endpoints (.git, .env, etc.)
- WordPress-like endpoints for attracting CMS scanners

### 3. Attack Pattern Recognition
- Real-time threat scoring based on request patterns
- Detection of common attack vectors:
  - SQL injection attempts
  - Command injection
  - Path traversal
  - Scanner tools (nmap, sqlmap, etc.)
- Attacker profiling and behavior tracking

### 4. Analytics Dashboard
- Visualize attack patterns and statistics
- Track top threats and most targeted resources
- Analyze attacker methodology and persistence

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the Honeypot

### Development Mode

```
python app.py
```

### Production Deployment

It's recommended to use Docker for production deployments:

```
docker build -t ai-honeypot .
docker run -p 5000:5000 ai-honeypot
```

## Configuration

The honeypot is designed to run with minimal configuration, but you can enhance its capabilities by:

1. Adding a real OpenAI API key for more sophisticated text generation
2. Implementing actual StyleGAN3 for image generation 
3. Customizing the attack detection patterns in `analytics.py`

## Security Considerations

This honeypot is designed to be deployed on isolated systems with proper monitoring. **Do not** deploy it alongside production systems or with access to sensitive data.

## Data Collection

The honeypot logs attack patterns and generates reports in the `analytics/` directory. These can be used for:

- Threat intelligence
- Understanding emerging attack patterns
- Security research and education
- Training machine learning models for attack detection

## License

MIT License 