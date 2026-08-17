import os, random, threading, time, datetime
import telebot
from telebot import types
from flask import Flask
from supabase import create_client

# ВАЖНО: токен задан пользователем для новой версии бота.
TOKEN = "8833519988:AAGoS8H4zWEpKQVoMuZeCqMNX5JWm9Hhvso"
ADMIN_ID = 7844240869
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://qsczqwjvirhochosdjap.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_KEY is required")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask(__name__)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------- ДАННЫЕ --------------------
ALL_BRAWLERS = [
    "Шелли","Кольт","Булл","Брок","Эль Примо","Барли","Поко","Роза","Рико","Дэррил",
    "Пенни","Пэм","Нита","Карл","Джеки","Гас","Мэнди","Хэнк","Пирс","Сэм","Базз",
    "Сэнди","Леон","Кроу","Спайк","Сёрдж","Колетт","Эдгар","Байрон","Стью","Фэнг",
    "Ворон","Драко","Мелоди","Луми","Дамиан","Сириус","Кенджи","Кадзэ","Нори","Джэ Ён",
    "Грифф","Мортис","Тара","Даг","Генерал Гавс","Биби","Вольт","Джин","Отис","8-бит","Белль"
]

MODES = {
    "🎯 Ограбление": {"win": 10, "loss": 5, "tokens": 100},
    "💀 Нокаут": {"win": 12, "loss": 6, "tokens": 120},
    "⚽ Бравлбол": {"win": 10, "loss": 5, "tokens": 110},
    "🏴‍☠️ Шоудаун": {"win": 15, "loss": 7, "tokens": 140},
    "👥 Парное столкновение": {"win": 14, "loss": 7, "tokens": 150},
    "🔥 Горячая зона": {"win": 11, "loss": 5, "tokens": 125},
    "✈️ Аэробой": {"win": 13, "loss": 6, "tokens": 135},
}

ROAD_REWARDS = {
    100: {"type":"coins","amount":100},
    500: {"type":"coins","amount":300},
    1000: {"type":"gems","amount":10},
    2500: {"type":"box","key":"большой","name":"Большой ящик"},
    5000: {"type":"brawler","name":"Кольт"},
    10000: {"type":"gems","amount":25},
    15000: {"type":"box","key":"мега","name":"Мега ящик"},
    20000: {"type":"brawler","name":"Леон"},
    30000: {"type":"coins","amount":2000},
    40000: {"type":"gems","amount":50},
    50000: {"type":"brawler","name":"Спайк"},
    65000: {"type":"box","key":"легендарный","name":"Легендарный ящик"},
    80000: {"type":"gems","amount":75},
    100000: {"type":"brawler","name":"Драко"},
    125000: {"type":"coins","amount":5000},
    150000: {"type":"gems","amount":100},
    175000: {"type":"brawler","name":"Ворон"},
    200000: {"type":"skin","name":"Призрачный всадник Драко"},
}

GIFTS = {
    "draco": {"brawler":"Драко","skin":"Призрачный всадник Драко","title":"БулькаБулькаКарабулька"},
    "karl": {"brawler":"Карл","skin":"Сёрфер Карл","title":"ЛЕТО ЗАКАНЧИВАЕТСЯ ЧЕРЕЗ 20 ДНЕЕЕЙ =((("},
}

# -------------------- СОСТОЯНИЕ --------------------
FIGHT_LOCK = threading.Lock()
ACTIVE_FIGHTS = set()
FIGHT_COOLDOWN = {}
ONLINE_QUEUE = {}  # uid -> {mode, joined_at}
ONLINE_LOCK = threading.Lock()


def now_ts():
    return time.time()


def get_player(uid, name="Player"):
    uid = str(uid)
    r = supabase.table("players").select("*").eq("uid", uid).execute()
    if r.data:
        p = r.data[0]
        p.setdefault("brawlers", ["Шелли"])
        p.setdefault("selected_brawler", "Шелли")
        p.setdefault("brawler_wins", {})
        p.setdefault("brawler_trophies", {})
        p.setdefault("claimed_road", [])
        p.setdefault("skins", [])
        p.setdefault("titles", [])
        p.setdefault("achievements", [])
        p.setdefault("boxes", {"обычный":0,"большой":0,"мега":0,"легендарный":0})
        p.setdefault("total_wins", 0); p.setdefault("total_losses", 0)
        p.setdefault("win_streak", 0); p.setdefault("max_win_streak", 0)
        p.setdefault("max_trophies", p.get("trophies", 0))
        return p
    p = {
        "uid": uid, "name": name, "trophies": 90, "coins": 500, "gems": 50,
        "brawlers":["Шелли"], "selected_brawler":"Шелли", "brawler_wins":{},
        "brawler_trophies":{"Шелли":90}, "win_streak":0, "max_win_streak":0,
        "max_trophies":90, "bp_tokens":0, "claimed_road":[], "skins":[], "titles":[],
        "achievements":[], "total_wins":0, "total_losses":0,
        "boxes":{"обычный":0,"большой":0,"мега":0,"легендарный":0}
    }
    supabase.table("players").insert(p).execute()
    return p


def update_player(uid, data):
    supabase.table("players").update(data).eq("uid", str(uid)).execute()


def safe_update(uid, data):
    try:
        update_player(uid, data)
        return True
    except Exception as e:
        print("DB update error:", e)
        return False


def give_box(p, key, count=1):
    boxes = dict(p.get("boxes") or {})
    boxes[key] = boxes.get(key, 0) + count
    p["boxes"] = boxes


def claim_road(uid):
    p = get_player(uid)
    claimed = list(p.get("claimed_road") or [])
    rewards = []
    for trophy, reward in ROAD_REWARDS.items():
        if p.get("trophies", 0) < trophy or trophy in claimed:
            continue
        typ = reward["type"]
        if typ == "coins":
            p["coins"] += reward["amount"]; rewards.append(f"💰 +{reward['amount']}")
        elif typ == "gems":
            p["gems"] += reward["amount"]; rewards.append(f"💎 +{reward['amount']}")
        elif typ == "box":
            give_box(p, reward["key"]); rewards.append(f"📦 {reward['name']}")
        elif typ == "brawler":
            if reward["name"] not in p["brawlers"]: p["brawlers"].append(reward["name"])
            rewards.append(f"🥊 {reward['name']}")
        elif typ == "skin":
            if reward["name"] not in p["skins"]: p["skins"].append(reward["name"])
            rewards.append(f"👕 {reward['name']}")
        claimed.append(trophy)
    p["claimed_road"] = claimed
    if rewards:
        safe_update(uid, {"coins":p["coins"],"gems":p["gems"],"boxes":p["boxes"],"brawlers":p["brawlers"],"skins":p["skins"],"claimed_road":claimed})
        bot.send_message(int(uid), "🎁 <b>Награды Пути к славе!</b>\n" + "\n".join(rewards))
    return rewards

# -------------------- /START --------------------
@bot.message_handler(commands=["start"])
def start(m):
    p = get_player(m.from_user.id, m.from_user.first_name)
    claim_road(m.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("⚔️ В бой!", "🛒 Магазин")
    markup.add("🥊 Мои бойцы", "🏆 Топ", "📜 Путь к славе")
    markup.add("👤 Мой профиль")
    greeting = f"<b>👋 Привет, {m.from_user.first_name}!</b>"
    text = (f"{greeting}\n\n🏆 Кубки: {p['trophies']}\n💰 Монеты: {p['coins']} | 💎 Гемы: {p['gems']}\n"
            f"🥊 Бойцов: {len(p['brawlers'])}\n🔥 Винстрик: {p.get('win_streak',0)}")
    bot.send_message(m.chat.id, text, reply_markup=markup)

# -------------------- БОЙ --------------------
def fight_buttons():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("🎯 Ограбление", "💀 Нокаут", "⚽ Бравлбол")
    m.add("🏴‍☠️ Шоудаун", "👥 Парное столкновение", "🔥 Горячая зона")
    m.add("✈️ Аэробой", "🌐 Онлайн бои", "◀️ Назад")
    return m

@bot.message_handler(func=lambda m: m.text == "⚔️ В бой!" and m.chat.type == "private")
def fight_menu(m):
    bot.send_message(m.chat.id, "🎮 <b>Выбери режим:</b>", reply_markup=fight_buttons())

@bot.message_handler(func=lambda m: m.text in MODES and m.chat.type == "private")
def bot_fight(m):
    uid = str(m.from_user.id)
    current = now_ts()
    with FIGHT_LOCK:
        if uid in ACTIVE_FIGHTS:
            bot.answer_callback_query if False else None
            bot.send_message(m.chat.id, "⏳ Текущий бой ещё обрабатывается.")
            return
        last = FIGHT_COOLDOWN.get(uid, 0)
        if current - last < 8:
            bot.send_message(m.chat.id, f"🛡️ Защита от спама: подожди {int(8-(current-last))+1} сек.")
            return
        FIGHT_COOLDOWN[uid] = current
        ACTIVE_FIGHTS.add(uid)
    try:
        p = get_player(uid)
        if p.get("banned"): return bot.send_message(m.chat.id, "❌ Ты забанен!")
        mode = MODES[m.text]
        selected = p.get("selected_brawler") or "Шелли"
        win = random.random() < 0.5
        bt = dict(p.get("brawler_trophies") or {})
        bw = dict(p.get("brawler_wins") or {})
        if win:
            gain = mode["win"]
            p["trophies"] += gain; p["bp_tokens"] = p.get("bp_tokens",0) + mode["tokens"]
            p["coins"] += random.randint(30,80); p["total_wins"] += 1
            p["win_streak"] = p.get("win_streak",0)+1; p["max_win_streak"] = max(p.get("max_win_streak",0),p["win_streak"])
            p["max_trophies"] = max(p.get("max_trophies",0),p["trophies"])
            bt[selected] = bt.get(selected,90)+gain; bw[selected] = bw.get(selected,0)+1
            text = f"🎉 <b>Победа!</b>\n{m.text}\n+{gain}🏆 +{mode['tokens']}🎟️\n🔥 Винстрик: {p['win_streak']}"
        else:
            loss = mode["loss"]
            p["trophies"] = max(0,p["trophies"]-loss); p["total_losses"] += 1; p["win_streak"] = 0
            bt[selected] = max(0,bt.get(selected,90)-loss)
            text = f"💔 <b>Поражение</b>\n{m.text}\n-{loss}🏆\n❌ Винстрик сброшен"
        p["brawler_trophies"] = bt; p["brawler_wins"] = bw
        safe_update(uid, {"trophies":p["trophies"],"coins":p["coins"],"bp_tokens":p.get("bp_tokens",0),"total_wins":p["total_wins"],"total_losses":p["total_losses"],"win_streak":p["win_streak"],"max_win_streak":p["max_win_streak"],"max_trophies":p["max_trophies"],"brawler_trophies":bt,"brawler_wins":bw})
        bot.send_message(m.chat.id, text)
        claim_road(uid)
    finally:
        with FIGHT_LOCK: ACTIVE_FIGHTS.discard(uid)

# -------------------- ОНЛАЙН БОИ С РЕАЛЬНЫМИ ИГРОКАМИ --------------------
@bot.message_handler(func=lambda m: m.text == "🌐 Онлайн бои" and m.chat.type == "private")
def online_menu(m):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for mode in MODES:
        markup.add(types.InlineKeyboardButton(mode, callback_data="online:"+mode))
    markup.add(types.InlineKeyboardButton("❌ Отменить поиск", callback_data="online_cancel"))
    bot.send_message(m.chat.id, "🌐 <b>Онлайн-бой</b>\nВыбери режим. Бот найдёт другого реального игрока, который тоже в очереди.", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("online:"))
def online_join(call):
    uid = str(call.from_user.id); mode = call.data.split(":",1)[1]
    with ONLINE_LOCK:
        opponent = next((u for u,v in ONLINE_QUEUE.items() if u != uid and v["mode"] == mode), None)
        if opponent:
            ONLINE_QUEUE.pop(opponent, None); ONLINE_QUEUE.pop(uid, None)
            p1 = get_player(opponent); p2 = get_player(uid)
        else:
            ONLINE_QUEUE[uid] = {"mode":mode,"joined_at":now_ts()}
            p1 = p2 = None
    if not opponent:
        bot.answer_callback_query(call.id, "🔎 Поиск соперника начат!")
        bot.send_message(call.message.chat.id, f"🔎 Ищу реального игрока в режиме <b>{mode}</b>...\nНичего нажимать повторно не нужно.")
        return
    # Небольшая антиспам-защита уже выполнена на входе в очередь.
    winner_uid = random.choice([opponent, uid])
    loser_uid = uid if winner_uid == opponent else opponent
    wp = p1 if winner_uid == opponent else p2; lp = p2 if winner_uid == opponent else p1
    gain = MODES[mode]["win"]; loss = MODES[mode]["loss"]
    for player, won in ((wp,True),(lp,False)):
        selected = player.get("selected_brawler") or "Шелли"
        bt = dict(player.get("brawler_trophies") or {})
        bw = dict(player.get("brawler_wins") or {})
        if won:
            player["trophies"] += gain; player["total_wins"] += 1; player["win_streak"] = player.get("win_streak",0)+1
            player["max_win_streak"] = max(player.get("max_win_streak",0),player["win_streak"]); player["coins"] += 60
            bt[selected] = bt.get(selected,90)+gain; bw[selected] = bw.get(selected,0)+1
        else:
            player["trophies"] = max(0,player.get("trophies",0)-loss); player["total_losses"] += 1; player["win_streak"] = 0
            bt[selected] = max(0,bt.get(selected,90)-loss)
        player["brawler_trophies"] = bt; player["brawler_wins"] = bw
        safe_update(player["uid"], {"trophies":player["trophies"],"coins":player["coins"],"total_wins":player["total_wins"],"total_losses":player["total_losses"],"win_streak":player["win_streak"],"max_win_streak":player["max_win_streak"],"brawler_trophies":bt,"brawler_wins":bw})
    bot.answer_callback_query(call.id, "⚔️ Соперник найден!")
    bot.send_message(int(winner_uid), f"🏆 <b>ОНЛАЙН ПОБЕДА!</b>\nРежим: {mode}\nПротивник: {lp['name']}\n+{gain}🏆")
    bot.send_message(int(loser_uid), f"💔 <b>ОНЛАЙН ПОРАЖЕНИЕ</b>\nРежим: {mode}\nПобедитель: {wp['name']}\n-{loss}🏆")
    claim_road(winner_uid); claim_road(loser_uid)

@bot.callback_query_handler(func=lambda c: c.data == "online_cancel")
def online_cancel(call):
    with ONLINE_LOCK: ONLINE_QUEUE.pop(str(call.from_user.id), None)
    bot.answer_callback_query(call.id, "❌ Поиск отменён")

# -------------------- ТОП --------------------
@bot.message_handler(func=lambda m: m.text == "🏆 Топ" and m.chat.type == "private")
def top_menu(m):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🏆 По кубкам", callback_data="top_trophies"))
    markup.add(types.InlineKeyboardButton("🥊 Топ по бойцам", callback_data="top_brawlers"))
    bot.send_message(m.chat.id, "🏆 <b>ТОП</b>", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "top_trophies")
def top_trophies(call):
    rows = supabase.table("players").select("uid,name,trophies").execute().data or []
    rows.sort(key=lambda x:x.get("trophies",0), reverse=True)
    medals=["🥇","🥈","🥉"]; text="🏆 <b>ТОП ПО КУБКАМ</b>\n\n"
    for i,p in enumerate(rows[:10]): text += f"{medals[i] if i<3 else str(i+1)+'.'} {p.get('name','Игрок')} — {p.get('trophies',0)}🏆\n"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda c: c.data == "top_brawlers")
def top_brawlers(call):
    rows = supabase.table("players").select("uid,name,brawler_trophies,brawlers").execute().data or []
    scored=[]
    for p in rows:
        bt=p.get("brawler_trophies") or {}; total=sum(int(v or 0) for v in bt.values()); best=max(bt.items(), key=lambda x:x[1], default=("Шелли",0))
        scored.append((total,p.get("name","Игрок"),best[0],best[1]))
    scored.sort(reverse=True)
    text="🥊 <b>ТОП ПО БОЙЦАМ</b>\n\n"
    for i,(total,name,brawler,best) in enumerate(scored[:10]): text += f"{i+1}. {name} — {total}🏆\n   ⭐ Лучший: {brawler} ({best}🏆)\n"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

# -------------------- ПУТЬ К СЛАВЕ --------------------
@bot.message_handler(func=lambda m: m.text == "📜 Путь к славе" and m.chat.type == "private")
def road(m):
    uid=str(m.from_user.id); p=get_player(uid); claim_road(uid); p=get_player(uid)
    text=f"📜 <b>ПУТЬ К СЛАВЕ</b>\n\n🏆 Кубки: {p.get('trophies',0)}/200000\n\n🎁 <b>Награды:</b>\n"
    for t,r in sorted(ROAD_REWARDS.items()):
        done='✅' if t in (p.get('claimed_road') or []) else ('🔓' if p.get('trophies',0)>=t else '🔒')
        if r['type']=='coins': reward=f"💰 {r['amount']}"
        elif r['type']=='gems': reward=f"💎 {r['amount']}"
        elif r['type']=='box': reward=f"📦 {r['name']}"
        elif r['type']=='brawler': reward=f"🥊 {r['name']}"
        else: reward=f"👕 {r['name']}"
        text += f"{done} {t:,}🏆 — {reward}\n"
    bot.send_message(m.chat.id,text)

# -------------------- МАГАЗИН / ПОДАРКИ --------------------
@bot.message_handler(func=lambda m: m.text == "🛒 Магазин" and m.chat.type == "private")
def shop(m):
    markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🎁 Подарки",callback_data="shop_gifts"))
    bot.send_message(m.chat.id,"🛒 <b>МАГАЗИН</b>\n\nВыбери раздел:",reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data=="shop_gifts")
def shop_gifts(call):
    p=get_player(call.from_user.id); claimed=set(p.get('achievements') or [])
    text="🎁 <b>ПОДАРКИ</b>\n\n"; markup=types.InlineKeyboardMarkup(row_width=1)
    for key,g in GIFTS.items():
        done=f"gift_{key}" in claimed
        text += f"🥊 {g['brawler']}\n👕 {g['skin']}\n🏷️ {g['title']}\n{'✅ Получено' if done else '🎁 Бесплатно'}\n\n"
        if not done: markup.add(types.InlineKeyboardButton(f"🎁 Забрать {g['brawler']}",callback_data=f"gift:{key}"))
    bot.edit_message_text(text,call.message.chat.id,call.message.message_id,reply_markup=markup)

@bot.callback_query_handler(func=lambda c:c.data.startswith("gift:"))
def claim_gift(call):
    key=call.data.split(":",1)[1]; g=GIFTS.get(key)
    if not g: return
    uid=str(call.from_user.id); p=get_player(uid); claimed=list(p.get('achievements') or []); marker=f"gift_{key}"
    if marker in claimed: return bot.answer_callback_query(call.id,"❌ Уже получено",show_alert=True)
    for field,val in (("brawlers",g['brawler']),("skins",g['skin']),("titles",g['title'])):
        arr=list(p.get(field) or []); 
        if val not in arr: arr.append(val)
        p[field]=arr
    claimed.append(marker); p['achievements']=claimed
    safe_update(uid,{"brawlers":p['brawlers'],"skins":p['skins'],"titles":p['titles'],"achievements":claimed})
    bot.answer_callback_query(call.id,"🎁 Подарок получен!")
    shop_gifts(call)

# -------------------- БОЙЦЫ / ПРОФИЛЬ --------------------
@bot.message_handler(func=lambda m:m.text=="🥊 Мои бойцы" and m.chat.type=="private")
def brawlers(m):
    p=get_player(m.from_user.id); text="🥊 <b>МОИ БОЙЦЫ</b>\n\n"; markup=types.InlineKeyboardMarkup(row_width=3)
    for b in p['brawlers']:
        text += f"{b}: {(p.get('brawler_trophies') or {}).get(b,90)}🏆 / {(p.get('brawler_wins') or {}).get(b,0)} побед\n"
        markup.add(types.InlineKeyboardButton(b,callback_data=f"sel:{b}"))
    bot.send_message(m.chat.id,text,reply_markup=markup)

@bot.callback_query_handler(func=lambda c:c.data.startswith("sel:"))
def select_brawler(call):
    b=call.data.split(":",1)[1]; p=get_player(call.from_user.id)
    if b not in p['brawlers']: return bot.answer_callback_query(call.id,"❌ Боец не найден",show_alert=True)
    safe_update(call.from_user.id,{"selected_brawler":b}); bot.answer_callback_query(call.id,f"✅ {b} выбран")

@bot.message_handler(func=lambda m:m.text=="👤 Мой профиль" and m.chat.type=="private")
def profile(m):
    p=get_player(m.from_user.id); bot.send_message(m.chat.id,f"👤 <b>{p['name']}</b>\n\n🏆 {p['trophies']} кубков\n🥊 {len(p['brawlers'])} бойцов\n🏆 Побед: {p.get('total_wins',0)}\n💔 Поражений: {p.get('total_losses',0)}\n🔥 Серия: {p.get('win_streak',0)}")

@bot.message_handler(func=lambda m:m.text=="◀️ Назад" and m.chat.type=="private")
def back(m): start(m)

@app.get("/")
def health(): return "Brawl Stars bot is running", 200

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0",port=int(os.getenv("PORT","10000")),use_reloader=False),daemon=True).start()
    print("Brawl Stars bot started")
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
