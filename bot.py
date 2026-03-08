import os
import random
import asyncio
import sqlite3
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = "USERNAMEBOTKAMU"
OWNER_ID = int(os.getenv("OWNER_ID"))
CHANNEL_USERNAME = "USERNAMECHANNELKAMU"
COOLDOWN = 3
# ==========================================

# ================= DATABASE =================
conn = sqlite3.connect("super_game.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS stats (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    total_play INTEGER DEFAULT 0,
    total_jackpot INTEGER DEFAULT 0,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1
)
""")

conn.commit()

cursor.execute("INSERT OR IGNORE INTO settings VALUES ('price','10')")
cursor.execute("INSERT OR IGNORE INTO settings VALUES ('revenue','0')")
cursor.execute("INSERT OR IGNORE INTO settings VALUES ('global_jackpot','0')")
conn.commit()

pending_game = {}
last_play_time = {}

# ================= SETTINGS =================
def get_setting(key):
    cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
    return cursor.fetchone()[0]

def set_setting(key, value):
    cursor.execute("UPDATE settings SET value=? WHERE key=?", (value, key))
    conn.commit()

def get_price():
    return int(get_setting("price"))

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    price = get_price()
    now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    premium_status = "Premium ⭐" if user.is_premium else "Standard 👤"

    photos = await context.bot.get_user_profile_photos(user.id)

    caption_text = (
        f"🎮 *WELCOME TO NFT GAME BOT* 🎮\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 Nama: {user.full_name}\n"
        f"🔗 Username: @{user.username}\n"
        f"🆔 ID: `{user.id}`\n"
        f"⭐ Status: {premium_status}\n"
        f"🕒 Login: {now}\n\n"
        f"💎 Harga Main: {price} Stars / Play\n"
        f"🔥 Kumpulkan XP • Naik Level • Raih Jackpot!\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🚀 Powered by NFT Game Bot"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎰 Main Slot 🎰", callback_data="slot"),
            InlineKeyboardButton("🎯 Main Dart 🎯", callback_data="dart"),
        ],
        [
            InlineKeyboardButton("📊 Statistik Saya 📊", callback_data="stats"),
            InlineKeyboardButton("🏆 Leaderboard Global 🏆", callback_data="leaderboard"),
        ],
        [
            InlineKeyboardButton("🎁 Claim Jackpot 🎁", callback_data="claim"),
        ],
        [
            InlineKeyboardButton("⭐ Top Up Stars ⭐", url=f"https://t.me/{BeliTonBot}?start=topup"),
        ],
        [
            InlineKeyboardButton("📢 Channel Hadiah 📢", url=f"https://t.me/{ktaal}"),
        ],
    ])

    if photos.total_count > 0:
        await update.message.reply_photo(
            photo=photos.photos[0][-1].file_id,
            caption=caption_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    else:
        await update.message.reply_text(
            caption_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )

# ================= BUTTON =================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()

    price = get_price()

    if query.data in ["slot", "dart"]:
        now = asyncio.get_event_loop().time()
        if user.id in last_play_time and now - last_play_time[user.id] < COOLDOWN:
            await query.message.reply_text("⏳ Tunggu sebentar sebelum main lagi ya...")
            return

        pending_game[user.id] = query.data

        prices = [LabeledPrice("🎮 1x Play NFT Game 🎮", price)]

        await context.bot.send_invoice(
            chat_id=user.id,
            title="🎟 Pembayaran NFT Game 🎟",
            description=f"💎 {price} Stars untuk 1x permainan hiburan",
            payload="play",
            provider_token="",
            currency="XTR",
            prices=prices,
        )

    elif query.data == "stats":
        cursor.execute("SELECT total_play,total_jackpot,xp,level FROM stats WHERE user_id=?", (user.id,))
        data = cursor.fetchone()
        if not data:
            await query.message.reply_text("📭 Kamu belum punya statistik permainan.")
            return

        play, jackpot, xp, level = data

        await query.message.reply_text(
            f"📊 *STATISTIK NFT GAME BOT* 📊\n\n"
            f"🎮 Total Play: {play}\n"
            f"🔥 Jackpot: {jackpot}\n"
            f"⭐ XP: {xp}\n"
            f"🏆 Level: {level}",
            parse_mode="Markdown"
        )

    elif query.data == "leaderboard":
        cursor.execute("""
            SELECT username,level,xp FROM stats
            ORDER BY level DESC, xp DESC
            LIMIT 10
        """)
        rows = cursor.fetchall()

        text = "🏆 *TOP 10 NFT GAME BOT* 🏆\n\n"
        for i, row in enumerate(rows, start=1):
            text += f"{i}. @{row[0]} | Lv {row[1]} | XP {row[2]}\n"

        await query.message.reply_text(text, parse_mode="Markdown")

    elif query.data == "claim":
        cursor.execute("SELECT total_jackpot FROM stats WHERE user_id=?", (user.id,))
        data = cursor.fetchone()

        if not data or data[0] < 1:
            await query.message.reply_text("❌ Kamu belum punya jackpot untuk diklaim.")
            return

        cursor.execute("UPDATE stats SET total_jackpot = total_jackpot - 1 WHERE user_id=?", (user.id,))
        conn.commit()

        await context.bot.send_message(
            OWNER_ID,
            f"🎁 CLAIM JACKPOT NFT GAME BOT 🎁\n\n👤 @{user.username}\n🆔 {user.id}"
        )

        await query.message.reply_text("✅ Claim berhasil dikirim ke admin 👑")

# ================= PAYMENT =================
async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    price = get_price()

    if user.id not in pending_game:
        return

    game_type = pending_game[user.id]
    del pending_game[user.id]

    last_play_time[user.id] = asyncio.get_event_loop().time()

    cursor.execute("INSERT OR IGNORE INTO stats (user_id,username) VALUES (?,?)",
                   (user.id, user.username))

    cursor.execute("UPDATE stats SET total_play=total_play+1 WHERE user_id=?", (user.id,))
    set_setting("revenue", str(int(get_setting("revenue")) + price))

    await update.message.reply_text("🎬 Mesin NFT Game sedang berputar... 🎰")
    await asyncio.sleep(2)

    xp_gain = random.randint(5, 15)

    if game_type == "slot":
        emojis = ["🍒", "🍋", "🍉", "⭐", "💎"]
        result = [random.choice(emojis) for _ in range(3)]

        if result[0] == result[1] == result[2]:
            cursor.execute("UPDATE stats SET total_jackpot=total_jackpot+1 WHERE user_id=?", (user.id,))
            set_setting("global_jackpot", str(int(get_setting("global_jackpot")) + 1))
            message = f"🎰 {' | '.join(result)}\n\n🔥 JACKPOT NFT STYLE!!! 🔥"
        else:
            message = f"🎰 {' | '.join(result)}\n\n😅 Belum hoki, coba lagi!"

    else:
        score = random.randint(1, 100)
        message = f"🎯 Skor Kamu: {score}\n\n🔥 Keren!"

    cursor.execute("UPDATE stats SET xp=xp+? WHERE user_id=?", (xp_gain, user.id))

    cursor.execute("SELECT xp,level FROM stats WHERE user_id=?", (user.id,))
    xp, level = cursor.fetchone()

    if xp >= level * 100:
        cursor.execute("UPDATE stats SET level=level+1 WHERE user_id=?", (user.id,))
        message += "\n\n🏆 LEVEL UP NFT MASTER!"

    conn.commit()

    await update.message.reply_text(message)

# ================= ADMIN =================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    revenue = get_setting("revenue")
    global_jackpot = get_setting("global_jackpot")
    price = get_price()

    await update.message.reply_text(
        f"👑 *NFT GAME BOT DASHBOARD* 👑\n\n"
        f"💎 Harga: {price}\n"
        f"💰 Revenue: {revenue} Stars\n"
        f"🔥 Global Jackpot: {global_jackpot}",
        parse_mode="Markdown"
    )

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    print("🚀 NFT GAME BOT RUNNING...")
    app.run_polling()

if __name__ == "__main__":
    main()
