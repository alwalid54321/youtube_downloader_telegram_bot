Here is the **README.md** written as **code block** so you can copy-paste directly:

````md
# 📥 Telegram Video Downloader Bot

A simple Telegram bot that downloads videos using **yt-dlp** and sends them back to users (max 50MB).  
Built using **python-telegram-bot v21+** with async support and threaded downloading.

---

## 🚀 Features

- Download videos from YouTube and many other sites  
- Real-time progress updates (percentage, speed, ETA)  
- Automatic upload after download completes  
- Max file size limited to **50MB**  
- Uses thread executor to avoid blocking the bot  
- Optional `cookies.txt` support for restricted videos  
- Handles errors cleanly (invalid URL, large file, login required)

---

## 📦 Requirements

Install dependencies:

```bash
pip install python-telegram-bot==21.4 yt-dlp
````

(Optional) If downloading login-required videos:

* Place a file named `cookies.txt` in the bot directory
* Export from browser using extensions like “Get Cookies.txt”

---

## 🔧 Configuration

Set your bot token using environment variable:

```bash
export BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
```

Or modify directly in the code (not recommended for production):

```python
BOT_TOKEN = "your-token-here"
```

---

## ▶️ Running the Bot

Run the bot with:

```bash
python main.py
```

You should see:

```
Bot is polling...
```

Now the bot is active.

---

## 🧩 Usage

1. Open your bot in Telegram
2. Send any **direct video link** (YouTube, Twitter, etc.)
3. Bot downloads and sends a video file back
4. If the file exceeds 50MB, you will receive a warning message

---

## 📁 File Structure

```
project/
│── main.py
│── cookies.txt   (optional)
│── README.md
└── requirements.txt (optional)
```

---

## ⚠️ Notes

* Telegram bots cannot upload files larger than 50MB
* Some YouTube videos require login; use cookies.txt
* If the bot stops updating progress, Telegram rate limits may apply
* Avoid too many concurrent downloads (limit is set to 4 threads)

---

## 🛠️ Troubleshooting

| Problem                    | Cause                           | Fix                       |
| -------------------------- | ------------------------------- | ------------------------- |
| “Sign-in required”         | Age-restricted or private video | Add cookies.txt           |
| “File is larger than 50MB” | Video too big                   | Choose lower quality link |
| Bot freezes at download    | Slow internet or blocked region | Try with cookies          |
| Instant failure            | Invalid URL                     | Check the link            |

---


```

