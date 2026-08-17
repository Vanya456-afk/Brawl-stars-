import os, subprocess, sys, time
RESTART_DELAY = int(os.getenv("BOT_RESTART_DELAY", "5"))
while True:
    print("🤖 Starting bot.py...", flush=True)
    process = subprocess.Popen([sys.executable, "-u", "bot.py"])
    code = process.wait()
    print(f"⚠️ bot.py stopped with exit code {code}. Restarting in {RESTART_DELAY}s...", flush=True)
    time.sleep(RESTART_DELAY)
