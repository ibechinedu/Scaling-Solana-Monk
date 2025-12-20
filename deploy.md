# Deployment Guide

## 🚀 Deploy to Railway

### Step 1: Prepare Your Repository
1. Push your code to GitHub
2. Ensure all sensitive data is in environment variables

### Step 2: Deploy to Railway
1. Go to [Railway.app](https://railway.app)
2. Sign up/Login with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway will auto-detect Python and deploy

### Step 3: Set Environment Variables
In Railway dashboard, go to Variables tab and add:

```
TELEGRAM_BOT_TOKEN=your_actual_bot_token
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
LOG_CHANNEL_ID=your_log_channel_id
ADMIN_GROUP_ID=your_admin_group_id  
BACKEND_GROUP_ID=your_backend_group_id
```

### Step 4: Monitor Deployment
- Check logs in Railway dashboard
- Bot should start automatically
- Test with /start command in Telegram

## 🔧 Local Development

```bash
# Clone repository
git clone your-repo-url
cd solana-trading-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your values

# Run bot
python telegrambot.py
```

## 📊 Monitoring
- Railway provides built-in monitoring
- Check logs for errors
- Monitor resource usage
- Set up alerts if needed