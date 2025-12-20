# 24/7 Deployment Guide for Scaling SolanaVM Bot

## Features Added
- ✅ Auto-restart on crash (max 100 attempts)
- ✅ Comprehensive error handling
- ✅ File + console logging
- ✅ Keep-alive ping every 10 minutes
- ✅ Skip old updates on restart
- ✅ Graceful shutdown handling

## Local Development
```bash
python telegrambot.py
```

## VPS Deployment (Ubuntu/Debian)

### 1. Install Dependencies
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### 2. Setup Bot
```bash
cd /home/ubuntu
git clone <your-repo> "SCALLING SOLANA BOT"
cd "SCALLING SOLANA BOT"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Systemd Service
```bash
sudo cp systemd_service.txt /etc/systemd/system/solana-bot.service
sudo systemctl daemon-reload
sudo systemctl enable solana-bot
sudo systemctl start solana-bot
sudo systemctl status solana-bot
```

### 4. View Logs
```bash
sudo journalctl -u solana-bot -f
# or
tail -f logs/bot.log
```

## Docker Deployment

### 1. Build and Run
```bash
docker-compose up -d
```

### 2. View Logs
```bash
docker-compose logs -f
```

### 3. Restart
```bash
docker-compose restart
```

## PM2 Deployment

### 1. Install PM2
```bash
npm install -g pm2
```

### 2. Start Bot
```bash
pm2 start pm2.config.js
pm2 save
pm2 startup
```

### 3. Monitor
```bash
pm2 status
pm2 logs scaling-solana-bot
pm2 monit
```

## Railway Deployment

### 1. Add to railway.toml
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python telegrambot.py"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

### 2. Environment Variables
- `TELEGRAM_BOT_TOKEN`: Your bot token

## Monitoring Commands

### Check if bot is running
```bash
# Systemd
sudo systemctl status solana-bot

# Docker
docker-compose ps

# PM2
pm2 status
```

### View real-time logs
```bash
# Systemd
sudo journalctl -u solana-bot -f

# Docker
docker-compose logs -f

# PM2
pm2 logs scaling-solana-bot --lines 100

# File logs
tail -f logs/bot.log
```

### Restart bot
```bash
# Systemd
sudo systemctl restart solana-bot

# Docker
docker-compose restart

# PM2
pm2 restart scaling-solana-bot
```

## Troubleshooting

### Bot not starting
1. Check logs for errors
2. Verify bot token is correct
3. Ensure all dependencies are installed
4. Check file permissions

### Bot keeps crashing
1. Check logs/bot.log for error details
2. Verify network connectivity
3. Check if Telegram API is accessible
4. Monitor memory usage

### Keep-alive not working
1. Check if bot has internet access
2. Verify Telegram API endpoints are reachable
3. Check firewall settings

## Log Files
- `logs/bot.log` - Main bot logs
- `logs/pm2-*.log` - PM2 specific logs (if using PM2)
- System logs via `journalctl` (if using systemd)