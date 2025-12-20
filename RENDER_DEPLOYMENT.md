# Render Deployment Guide for Solana Trading Bot

## Prerequisites
1. GitHub account
2. Render account (free tier available)
3. Telegram Bot Token from BotFather

## Step 1: Prepare Your Repository
1. Push this code to a GitHub repository
2. Ensure all files are committed:
   - `telegrambot.py`
   - `requirements.txt`
   - `render.yaml`
   - `health_check.py`
   - `.env.example`

## Step 2: Deploy on Render

### Option A: Using render.yaml (Recommended)
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New" → "Blueprint"
3. Connect your GitHub repository
4. Render will automatically detect `render.yaml`
5. Set environment variables (see below)

### Option B: Manual Setup
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `solana-trading-bot`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python telegrambot.py`

## Step 3: Environment Variables
Set these in Render Dashboard → Service → Environment:

### Required Variables:
- `TELEGRAM_BOT_TOKEN`: Your bot token from BotFather
- `SOLANA_RPC_URL`: `https://api.mainnet-beta.solana.com`

### Optional Variables:
- `LOG_CHANNEL_ID`: Telegram channel ID for logs
- `ADMIN_GROUP_ID`: Admin group ID
- `BACKEND_GROUP_ID`: Backend group ID

## Step 4: Deploy
1. Click "Create Web Service"
2. Render will build and deploy automatically
3. Monitor logs for any errors
4. Test your bot on Telegram

## Important Notes:
- Free tier has 750 hours/month (sufficient for most bots)
- Service sleeps after 15 minutes of inactivity
- First request after sleep may take 30+ seconds
- For 24/7 operation, upgrade to paid plan ($7/month)

## Troubleshooting:
- Check build logs if deployment fails
- Verify environment variables are set correctly
- Ensure your bot token is valid
- Test locally first with `python telegrambot.py`

## Health Check:
Run `python health_check.py` to verify bot configuration before deployment.