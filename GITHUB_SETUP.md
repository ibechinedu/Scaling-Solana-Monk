# GitHub Setup Instructions

## Step 1: Create GitHub Repository
1. Go to https://github.com
2. Click "New repository" (green button)
3. Repository name: `solana-trading-bot`
4. Description: `Telegram Trading Bot for Solana Blockchain`
5. Set to Public or Private
6. DO NOT initialize with README (we already have files)
7. Click "Create repository"

## Step 2: Push to GitHub
After creating the repository, GitHub will show you commands. Use these:

```bash
git branch -M main
git remote add origin https://github.com/YOURUSERNAME/YOURREPONAME.git
git push -u origin main
```

Replace YOURUSERNAME and YOURREPONAME with your actual GitHub username and repository name.

## Step 3: Deploy on Render
1. Go to https://render.com
2. Click "New" → "Blueprint"
3. Connect your GitHub repository
4. Set environment variable: TELEGRAM_BOT_TOKEN
5. Deploy!

Your repository is ready to push! 🚀