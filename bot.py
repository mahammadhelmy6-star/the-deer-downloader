import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# التوكن الخاص بك
TOKEN = "8777066204:AAH1eMKtG_oGZevuJW0mTbW7AOZAgiYwd84"

def get_formats(url):
    ydl_opts = {'quiet': True, 'noplaylist': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info.get('formats', [])
        available = []
        seen_heights = set()
        for f in formats:
            height = f.get('height')
            if height and height not in seen_heights and f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                available.append({'id': f['format_id'], 'res': f'{height}p'})
                seen_heights.add(height)
        return sorted(available, key=lambda x: int(x['res'][:-1]), reverse=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك يا أستاذنا! أرسل لي رابط الفيديو وسأعرض لك الجودات المتاحة.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith('http'): return
    msg = await update.message.reply_text("🔍 جاري فحص الرابط...")
    try:
        formats = get_formats(url)
        keyboard = [[InlineKeyboardButton(f"تحميل {f['res']}", callback_data=f"{f['id']}|{url}")] for f in formats[:5]]
        await msg.edit_text("اختر الجودة المطلوبة:", reply_markup=InlineKeyboardMarkup(keyboard))
    except:
        await msg.edit_text("عذراً، تعذر جلب الجودات. جرب رابطاً آخر.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    f_id, url = query.data.split('|')
    await query.edit_message_text("⏳ جاري التحميل والرفع تليجرام... انتظر قليلاً.")
    name = f"video_{query.from_user.id}.mp4"
    try:
        ydl_opts = {'format': f_id, 'outtmpl': name}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        await query.message.reply_video(video=open(name, 'rb'), caption="تم التحميل بنجاح ✅")
    except:
        await query.message.reply_text("فشل التحميل. قد يكون حجم الفيديو كبيراً جداً.")
    finally:
        if os.path.exists(name): os.remove(name)

if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.run_polling(drop_pending_updates=True)
