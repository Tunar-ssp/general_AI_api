# AI API Management System - Deployment Guide

## Global Deployment Options

This guide provides instructions for deploying the AI API Management System globally, making it accessible from anywhere.

## Option 1: Docker Deployment (Recommended)

### Prerequisites
- Docker and Docker Compose installed on your server
- Basic understanding of Docker and networking

### Steps

1. **Clone the repository to your server**

2. **Configure environment variables**
   - Copy `.env.example` to `.env`
   - Fill in your API keys and other configuration
   - Make sure to set a strong `ADMIN_API_KEY` or let the system generate one on first startup

3. **Build and start the containers**
   ```bash
   docker-compose up -d
   ```

4. **Access the API**
   - The API will be available at `http://your-server-ip:8000`
   - Use your admin API key to create additional API keys for users

5. **Security considerations**
   - Consider setting up a reverse proxy with HTTPS (like Nginx or Traefik)
   - Restrict access to the admin endpoints
   - Use a firewall to limit access to your server

## Option 2: Manual Deployment

### Prerequisites
- Python 3.9+ installed on your server
- PostgreSQL database
- Redis server

### Steps

1. **Clone the repository to your server**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   - Copy `.env.example` to `.env`
   - Fill in your API keys and database connection details
   - Set the `APP_URL` to your server's public URL

4. **Start the application**
   ```bash
   python main.py
   ```
   
   For production, consider using a process manager like Supervisor or systemd.

5. **Set up a reverse proxy (recommended)**
   - Configure Nginx or Apache to proxy requests to your application
   - Set up SSL/TLS certificates for HTTPS

## Option 3: Cloud Deployment

### AWS Elastic Beanstalk

1. Install the EB CLI
2. Initialize your EB application
3. Deploy with `eb deploy`

### Google Cloud Run

1. Build your Docker image
2. Push to Google Container Registry
3. Deploy to Cloud Run

### Azure App Service

1. Create an App Service plan
2. Deploy using Azure CLI or GitHub Actions

## API Authentication

The API uses API key authentication. All endpoints except the root and health check require an API key.

### Managing API Keys

1. **Create a new API key** (admin only)
   ```
   POST /api/admin/keys
   {
     "name": "user_name",
     "role": "user"
   }
   ```

2. **List all API keys** (admin only)
   ```
   GET /api/admin/keys
   ```

3. **Revoke an API key** (admin only)
   ```
   DELETE /api/admin/keys/{key_prefix}
   ```

### Using API Keys

Include the API key in all requests using one of these methods:

- HTTP header: `X-API-Key: your-api-key`
- Query parameter: `?X-API-Key=your-api-key`

## Monitoring and Maintenance

- Check logs in the `logs` directory
- Monitor API usage with the `/api/ai/stats` endpoint
- Regularly backup your database

## Troubleshooting

- If the API is not accessible, check your firewall settings
- For database connection issues, verify your PostgreSQL configuration
- For Redis connection issues, check your Redis server status

## Security Best Practices

1. Always use HTTPS in production
2. Regularly rotate API keys
3. Keep your server and dependencies updated
4. Monitor for suspicious activity
5. Implement rate limiting at the network level