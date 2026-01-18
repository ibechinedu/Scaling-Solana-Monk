# Choreo Deployment Guide for Solana Trading Bot

## Prerequisites
- WSO2 Choreo account (https://console.choreo.dev/)
- GitHub repository with your bot code
- Telegram Bot Token from BotFather

## Deployment Steps

### 1. Prepare Your Repository
Ensure your repository contains:
- `telegrambot.py` (main bot file)
- `requirements.txt` (dependencies)
- `Dockerfile.choreo` (container configuration)
- `.choreo/component.yaml` (Choreo configuration)
- `health_server.py` (health check endpoint)

### 2. Create Component in Choreo

1. Login to Choreo Console
2. Click "Create Component"
3. Select "Service" type
4. Choose "Dockerfile" as build method
5. Connect your GitHub repository
6. Set Dockerfile path: `Dockerfile.choreo`
7. Set component name: `solana-trading-bot`

### 3. Configure Environment Variables

In Choreo Console, go to your component settings and add:

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
LOG_CHANNEL_ID=your_log_channel_id (optional)
ADMIN_GROUP_ID=your_admin_group_id (optional)
BACKEND_GROUP_ID=your_backend_group_id (optional)
PORT=8080
```

### 4. Deploy

1. Click "Deploy" in Choreo Console
2. Wait for build and deployment to complete
3. Your bot will be accessible at the provided endpoint

### 5. Monitor

- Use Choreo's built-in monitoring
- Check logs in the Console
- Health endpoint: `https://your-app-url/health`

## Important Notes

- The bot runs in polling mode (no webhook required)
- Health check endpoint is available at `/health`
- Logs are written to both file and stdout
- Auto-restart functionality is built-in

## Troubleshooting

1. **Build Fails**: Check Dockerfile.choreo syntax
2. **Bot Not Responding**: Verify TELEGRAM_BOT_TOKEN
3. **Health Check Fails**: Ensure port 8080 is exposed
4. **Memory Issues**: Consider upgrading Choreo plan

## File Structure
```
├── .choreo/
│   └── component.yaml
├── .choreoignore
├── Dockerfile.choreo
├── health_server.py
├── telegrambot.py
├── requirements.txt
└── README.md
```