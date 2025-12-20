module.exports = {
  apps: [{
    name: 'scaling-solana-bot',
    script: 'telegrambot.py',
    interpreter: 'python3',
    cwd: '/path/to/SCALLING SOLANA BOT',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production'
    },
    error_file: './logs/pm2-error.log',
    out_file: './logs/pm2-out.log',
    log_file: './logs/pm2-combined.log',
    time: true,
    restart_delay: 5000,
    max_restarts: 10,
    min_uptime: '10s'
  }]
};