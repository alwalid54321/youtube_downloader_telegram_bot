import os
import logging
import glob
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, constants
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import yt_dlp

# --- CONFIGURATION ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "BOT_TOK")

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Thread pool for running blocking downloads
thread_pool = ThreadPoolExecutor(max_workers=4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Hi! Send me a link to a video, and I'll download it for you. (Max 50MB)"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Paste a URL. If downloads fail, the admin may need to update 'cookies.txt'."
    )

def download_video_sync(url, file_id, progress_hook=None):
    """
    Synchronous function to run inside a separate thread.
    """
    cookie_file = 'cookies.txt' if os.path.exists('cookies.txt') else None
    
    ydl_opts = {
        'outtmpl': f'{file_id}.%(ext)s',
        'format': 'best[ext=mp4]/best',
        'max_filesize': 50 * 1024 * 1024, # 50MB Telegram Limit
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        # Spoof User Agent
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    if progress_hook:
        ydl_opts['progress_hooks'] = [progress_hook]

    if cookie_file:
        ydl_opts['cookiefile'] = cookie_file

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            files = glob.glob(f"{file_id}.*")
            if files:
                return True, files[0], info.get('title', 'Video')
            return False, "File not found after download.", None
            
    except yt_dlp.utils.DownloadError as e:
        return False, str(e), None
    except Exception as e:
        return False, f"Internal Error: {str(e)}", None

async def download_and_send_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    chat_id = update.effective_chat.id

    if not url.startswith(('http://', 'https://')):
        await context.bot.send_message(chat_id=chat_id, text="❌ Invalid URL.")
        return

    # 1. Send Initial Status Message
    status_msg = await context.bot.send_message(
        chat_id=chat_id, 
        reply_to_message_id=update.message.message_id,
        text="🔍 Found link! Initializing download..."
    )
    await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.TYPING)

    file_id = f"video_{update.message.message_id}"
    last_update_time = 0
    
    # [FIX] Capture the main event loop here, before entering the thread
    main_loop = asyncio.get_running_loop()

    # --- Progress Hook (Runs in a separate Thread) ---
    def progress_hook(d):
        nonlocal last_update_time
        if d['status'] == 'downloading':
            current_time = time.time()
            # Update UI max once every 2 seconds to avoid flooding Telegram API
            if current_time - last_update_time > 2.0: 
                percent = d.get('_percent_str', '0%')
                eta = d.get('_eta_str', '?')
                speed = d.get('_speed_str', '?')
                
                text = f"⬇️ Downloading: {percent}\n🚀 Speed: {speed}\n⏳ ETA: {eta}"
                
                # [FIX] Use run_coroutine_threadsafe with main_loop captured earlier
                asyncio.run_coroutine_threadsafe(
                    context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=status_msg.message_id,
                        text=text
                    ),
                    main_loop
                )
                last_update_time = current_time

    # --- Run Blocking Download in Thread ---
    # We pass the 'main_loop' context is not needed here, but the hook uses it
    success, result, title = await main_loop.run_in_executor(
        thread_pool, 
        download_video_sync, 
        url, 
        file_id, 
        progress_hook
    )

    if success:
        video_path = result
        try:
            # 2. Update Status to Uploading
            await context.bot.edit_message_text(
                chat_id=chat_id, 
                message_id=status_msg.message_id, 
                text=f"✅ Download complete!\n⬆️ Uploading: {title}..."
            )
            await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.UPLOAD_VIDEO)
            
            # Send the video
            with open(video_path, 'rb') as f:
                await context.bot.send_video(
                    chat_id=chat_id,
                    video=f,
                    caption=f"🎥 {title}",
                    reply_to_message_id=update.message.message_id,
                    read_timeout=120, 
                    write_timeout=120, 
                    connect_timeout=120
                )
            
            # Delete status message on success
            await context.bot.delete_message(chat_id=chat_id, message_id=status_msg.message_id)
            
        except Exception as e:
            logging.error(f"Upload Error: {e}")
            await context.bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text=f"❌ Upload failed: {e}")
        finally:
            if os.path.exists(video_path):
                os.remove(video_path)
    else:
        # result contains error message here
        error_msg = result
        if "Sign in" in error_msg:
             await context.bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text="❌ YouTube Error: Sign-in required. (Cookies needed)")
        elif "File is larger than" in error_msg:
             await context.bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text="❌ Video is too large (>50MB).")
        else:
             await context.bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text="❌ Download Failed (Link valid? Geo-blocked?)")
        logging.error(f"Download failed: {error_msg}")

if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_and_send_video))

    print("Bot is polling...")
    application.run_polling()
