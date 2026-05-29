import os
import time
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
import instaloader

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = str(os.getenv("CHAT_ID"))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 300))

app = Application.builder().token(BOT_TOKEN).build()

L = instaloader.Instaloader(
    download_pictures=False,
    download_videos=False,
    download_video_thumbnails=False,
    save_metadata=False,
    compress_json=False,
)

sent_reels = set()


# =========================
# USERNAME SYSTEM
# =========================


def load_usernames():
    if not os.path.exists("usernames.txt"):
        open("usernames.txt", "w").close()

    with open("usernames.txt", "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]



def save_usernames(usernames):
    with open("usernames.txt", "w", encoding="utf-8") as f:
        for username in usernames:
            f.write(username + "\n")


# =========================
# TELEGRAM COMMANDS
# =========================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🔥 Instagram Reel Monitor Bot Started"
        "Commands:"
        "/add username"
        "/remove username"
        "/list"
        "/status"
    )

    await update.message.reply_text(text)


async def add_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /add username")
        return

    username = context.args[0].replace("@", "").lower()

    usernames = load_usernames()

    if username in usernames:
        await update.message.reply_text("⚠️ Username already exists")
        return

    usernames.append(username)
    save_usernames(usernames)

    await update.message.reply_text(f"✅ Added: @{username}")


async def remove_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /remove username")
        return

    username = context.args[0].replace("@", "").lower()

    usernames = load_usernames()

    if username not in usernames:
        await update.message.reply_text("❌ Username not found")
        return

    usernames.remove(username)
    save_usernames(usernames)

    await update.message.reply_text(f"🗑 Removed: @{username}")


async def list_usernames(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usernames = load_usernames()

    if not usernames:
        await update.message.reply_text("No usernames added")
        return

    text = "📋 Monitoring Accounts:"

    for user in usernames:
        text += f"• @{user}"

    await update.message.reply_text(text)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usernames = load_usernames()

    text = (
        "🤖 Bot Running Successfully"
        f"👥 Total Accounts: {len(usernames)}"
        f"⏱ Check Interval: {CHECK_INTERVAL} sec"
    )

    await update.message.reply_text(text)


# =========================
# REEL CHECKER
# =========================


async def send_notification(username, shortcode):
    reel_url = f"https://www.instagram.com/reel/{shortcode}/"

    text = (
        f"🔥 New Reel Uploaded\n\n"
        f"👤 Username: @{username}\n"
        f"🎬 Reel Link:\n{reel_url}"
    )

    await app.bot.send_message(chat_id=CHAT_ID, text=text)


async def check_reels():
    while True:
        usernames = load_usernames()

        for username in usernames:
            try:
                profile = instaloader.Profile.from_username(
                    L.context,
                    username,
                )

                for post in profile.get_posts():
                    if (
                        post.is_video
                        and post.shortcode not in sent_reels
                    ):
                        sent_reels.add(post.shortcode)

                        if post.typename == "GraphVideo":
                            await send_notification(
                                username,
                                post.shortcode,
                            )

                        break

            except Exception as e:
                print(f"Error checking {username}: {e}")

        await asyncio.sleep(CHECK_INTERVAL)


# =========================
# MAIN
# =========================


async def post_init(application):
    asyncio.create_task(check_reels())


app.post_init = post_init

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("add", add_username))
app.add_handler(CommandHandler("remove", remove_username))
app.add_handler(CommandHandler("list", list_usernames))
app.add_handler(CommandHandler("status", status))


if __name__ == "__main__":
    print("Instagram Reel Monitor Bot Started...")
    app.run_polling()
