# main.py
import asyncio
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from config import TELEGRAM_BOT_TOKEN, POLL_INTERVAL_SECONDS
from db import (
    init_db, add_subscription, remove_subscription,
    get_user_subscriptions, get_all_active_targets,
    is_post_seen, mark_post_seen
)
from fetcher import fetch_latest_posts, fetch_post_by_url

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Argon Feed Bot!\n\n"
        "Commands:\n"
        "• /add <username> - Track a creator's reels\n"
        "• /remove <username> - Stop tracking\n"
        "• /list - View your tracked creators\n\n"
        "💡 *Tip:* Send any Instagram Reel or Post link directly into chat to fetch it!",
        parse_mode="Markdown"
    )

async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/add username`", parse_mode="Markdown")
        return

    username = context.args[0].lower().lstrip("@")
    chat_id = update.effective_chat.id

    success = await add_subscription(chat_id, username)
    if success:
        current_posts = fetch_latest_posts(username)
        for post in current_posts:
            await mark_post_seen(username, post["id"])
        await update.message.reply_text(f"✅ Now tracking @{username}. You will only receive new reels going forward.")
    else:
        await update.message.reply_text(f"⚠️ You are already tracking @{username}.")

async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/remove username`", parse_mode="Markdown")
        return

    username = context.args[0].lower().lstrip("@")
    chat_id = update.effective_chat.id

    removed = await remove_subscription(chat_id, username)
    if removed:
        await update.message.reply_text(f"🗑️ Removed @{username}.")
    else:
        await update.message.reply_text(f"⚠️ @{username} is not in your list.")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subs = await get_user_subscriptions(chat_id)
    if not subs:
        await update.message.reply_text("Your list is empty. Add someone using `/add username`.", parse_mode="Markdown")
        return

    text = "📋 Tracked Creators:\n\n" + "\n".join([f"• @{u}" for u in subs])
    await update.message.reply_text(text)

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    # Matches /reel/, /reels/, /p/, and /tv/
    ig_pattern = r"(https?://(?:www\.)?instagram\.com/(?:reel|reels|p|tv)/[A-Za-z0-9_-]+)"
    match = re.search(ig_pattern, text)

    if not match:
        return

    target_url = match.group(1)
    status_msg = await update.message.reply_text("⏳ Fetching reel...")

    media_data = fetch_post_by_url(target_url)
    if not media_data or not media_data.get("media_url"):
        await status_msg.edit_text("❌ Couldn't retrieve media. The post might be private or unavailable.")
        return

    caption = media_data.get("caption", "")
    try:
        if media_data["is_video"]:
            await update.message.reply_video(video=media_data["media_url"], caption=caption)
        else:
            await update.message.reply_photo(photo=media_data["media_url"], caption=caption)
        await status_msg.delete()
    except Exception:
        await status_msg.edit_text(f"Here is your media link:\n{media_data['media_url']}")

async def poll_updates(context: ContextTypes.DEFAULT_TYPE):
    targets = await get_all_active_targets()
    user_to_chats = {}
    for username, chat_id in targets:
        user_to_chats.setdefault(username, []).append(chat_id)

    for username, chat_ids in user_to_chats.items():
        posts = fetch_latest_posts(username)
        for post in reversed(posts):
            if not await is_post_seen(post["id"]):
                caption_msg = f"🎬 New Reel from @{username}\n\n{post['caption']}\n\n🔗 {post['url']}"
                for cid in chat_ids:
                    try:
                        if post["is_video"] and post["media_url"]:
                            await context.bot.send_video(chat_id=cid, video=post["media_url"], caption=caption_msg)
                        elif post["media_url"]:
                            await context.bot.send_photo(chat_id=cid, photo=post["media_url"], caption=caption_msg)
                        else:
                            await context.bot.send_message(chat_id=cid, text=caption_msg)
                    except Exception:
                        await context.bot.send_message(chat_id=cid, text=caption_msg)

                await mark_post_seen(username, post["id"])
        await asyncio.sleep(2)

def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_user))
    app.add_handler(CommandHandler("remove", remove_user))
    app.add_handler(CommandHandler("list", list_users))
    
    # Message handler for direct Instagram URLs
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    app.job_queue.run_repeating(poll_updates, interval=POLL_INTERVAL_SECONDS, first=10)

    print("Argon bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()