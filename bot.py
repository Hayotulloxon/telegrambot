from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ContextTypes
)
import logging
import re
import os
import asyncio
import aiohttp
from datetime import datetime
import urllib.request
import urllib.parse
import json

# Bot sozlamalari
TOKEN = '7987802742:AAEVZTrn1_8w0l601bLMn4O-ONiw4w9PWNA'
YOUTUBE_CHANNEL_URL = 'https://www.youtube.com/@Sonic_edits-c4e'
YOUTUBE_API_KEY = 'YOUR_YOUTUBE_API_KEY'  # YouTube API kalitingizni bu yerga kiriting

# Loglash tizimi
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot_logs.log'  # Log faylini saqlash
)
logger = logging.getLogger(__name__)

# Foydalanuvchi xabarlarini kuzatish
user_stats = {}

# Emojilari
EMOJI = {
    "youtube": "📺",
    "download": "⬇️",
    "audio": "🎧",
    "video": "📹",
    "loading": "⏳",
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
    "subscribe": "📲",
    "quality": "🔍",
    "help": "❓"
}

# YouTube video ID'ni olish uchun
def extract_video_id(url):
    if 'youtu.be' in url:
        return url.split('/')[-1].split('?')[0]
    elif 'youtube.com/watch' in url:
        return urllib.parse.parse_qs(urllib.parse.urlparse(url).query)['v'][0]
    elif 'youtube.com/shorts' in url:
        return url.split('/')[-1].split('?')[0]
    return None

# YouTube video ma'lumotlarini olish uchun
async def get_video_info(video_id):
    try:
        url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={YOUTUBE_API_KEY}&part=snippet,contentDetails,statistics"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                if 'items' in data and len(data['items']) > 0:
                    video_data = data['items'][0]
                    snippet = video_data.get('snippet', {})
                    content_details = video_data.get('contentDetails', {})
                    
                    # Video davomiyligini olish
                    duration = content_details.get('duration', 'PT0M0S')
                    # ISO 8601 formatidan oddiy formatga o'tkazish
                    duration = duration.replace('PT', '').replace('H', ':').replace('M', ':').replace('S', '')
                    
                    return {
                        'title': snippet.get('title', 'Video'),
                        'description': snippet.get('description', ''),
                        'channelTitle': snippet.get('channelTitle', 'Unknown'),
                        'publishedAt': snippet.get('publishedAt', ''),
                        'thumbnail': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                        'duration': duration
                    }
                else:
                    return None
    except Exception as e:
        logger.error(f"YouTube API error: {str(e)}")
        return None

async def check_subscription(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    """Foydalanuvchi obunasini tekshirish"""
    return context.user_data.get(f'subscribed_{user_id}', False)

def restricted(func):
    """Decorator: Faqat obuna bo'lganlar uchun ruxsat"""
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if await check_subscription(context, user_id):
            return await func(update, context, *args, **kwargs)
        else:
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(f"{EMOJI['subscribe']} YouTube kanaliga obuna bo'lish", url=YOUTUBE_CHANNEL_URL),
                    InlineKeyboardButton(f"{EMOJI['success']} Obunani tasdiqlash", callback_data="confirm_subscribe")
                ],
                [InlineKeyboardButton(f"{EMOJI['help']} Yordam", callback_data="help")]
            ])
            
            await update.message.reply_text(
                f"{EMOJI['warning']} *Botdan foydalanish uchun avval YouTube kanalimizga obuna bo'ling!*",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            return
    return wrapped

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Boshlang'ich xabar"""
    user = update.effective_user
    user_id = user.id
    subscribed = await check_subscription(context, user_id)
    
    # Foydalanuvchi statistikasini yangilash
    if user_id not in user_stats:
        user_stats[user_id] = {
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "join_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "downloads": 0
        }
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"{EMOJI['subscribe']} YouTube kanaliga obuna bo'lish", url=YOUTUBE_CHANNEL_URL),
            InlineKeyboardButton(f"{EMOJI['success']} Obunani tasdiqlash", callback_data="confirm_subscribe")
        ],
        [InlineKeyboardButton(f"{EMOJI['help']} Yordam", callback_data="help")]
    ])
    
    welcome_text = (
        f"*Assalomu alaykum, {user.first_name}!* 👋\n\n"
        f"{EMOJI['youtube']} *YouTube Downloader Bot*ga xush kelibsiz!\n\n"
    )
    
    if not subscribed:
        welcome_text += (
            f"{EMOJI['warning']} Botdan foydalanish uchun avval YouTube kanalimizga obuna bo'ling.\n"
            f"Obunani tasdiqlash uchun quyidagi tugmalardan foydalaning."
        )
    else:
        welcome_text += (
            f"{EMOJI['info']} YouTube video havolasini yuboring, men uni yuklab beraman.\n\n"
            f"*Qo'llab-quvvatlanadigan havolalar:*\n"
            f"✓ YouTube video\n"
            f"✓ YouTube Shorts\n\n"
            f"Yordam uchun /help buyrug'idan foydalaning."
        )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=keyboard if not subscribed else None,
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Yordam xabarini ko'rsatish"""
    help_text = (
        f"*{EMOJI['youtube']} YouTube Downloader Bot - Qo'llanma*\n\n"
        f"Bu bot YouTube videolarini yuklab olishga yordam beradi.\n\n"
        f"*Asosiy buyruqlar:*\n"
        f"🔹 /start - Botni ishga tushirish\n"
        f"🔹 /help - Ushbu yordam xabarini ko'rsatish\n\n"
        f"*Qanday foydalanish mumkin:*\n"
        f"1. Istalgan YouTube video havolasini botga yuboring\n"
        f"2. Bot sizga audio yoki video formatini tanlash imkonini beradi\n"
        f"3. Sizga kerakli formatni tanlang\n"
        f"4. Yuklab olish tugagach, fayl avtomatik ravishda yuboriladi\n\n"
        f"*Eslatma:* Katta hajmdagi fayllarni yuklash ko'proq vaqt olishi mumkin."
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{EMOJI['subscribe']} YouTube kanaliga o'tish", url=YOUTUBE_CHANNEL_URL)]
    ])
    
    await update.message.reply_text(
        help_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Yordam tugmasi bosilganda"""
    query = update.callback_query
    await query.answer()
    
    help_text = (
        f"*{EMOJI['youtube']} YouTube Downloader Bot - Qo'llanma*\n\n"
        f"Bu bot YouTube videolarini yuklab olishga yordam beradi.\n\n"
        f"*Asosiy buyruqlar:*\n"
        f"🔹 /start - Botni ishga tushirish\n"
        f"🔹 /help - Ushbu yordam xabarini ko'rsatish\n\n"
        f"*Qanday foydalanish mumkin:*\n"
        f"1. Istalgan YouTube video havolasini botga yuboring\n"
        f"2. Bot sizga audio yoki video formatini tanlash imkonini beradi\n"
        f"3. Sizga kerakli formatni tanlang\n"
        f"4. Yuklab olish tugagach, fayl avtomatik ravishda yuboriladi\n\n"
        f"*Eslatma:* Katta hajmdagi fayllarni yuklash ko'proq vaqt olishi mumkin."
    )
    
    await query.edit_message_text(
        help_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{EMOJI['subscribe']} YouTube kanaliga o'tish", url=YOUTUBE_CHANNEL_URL)]
        ])
    )

async def confirm_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Obunani tasdiqlash"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    context.user_data[f'subscribed_{user_id}'] = True
    
    await query.edit_message_text(
        f"{EMOJI['success']} *Obuna muvaffaqiyatli tasdiqlandi!*\n\n"
        f"{EMOJI['info']} Endi YouTube havolasini yuborishingiz mumkin.\n\n"
        f"*Misol:* https://youtu.be/abcd1234",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{EMOJI['help']} Yordam", callback_data="help")]
        ])
    )

@restricted
async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Video yuklab olish"""
    try:
        url = update.message.text
        user_id = update.effective_user.id
        
        # Yuklanayotganini xabar berish
        status_message = await update.message.reply_text(
            f"{EMOJI['loading']} *Video ma'lumotlari tahlil qilinmoqda...*",
            parse_mode="Markdown"
        )
        
        # YouTube havolasi formatini tekshirish
        if not re.match(r'^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$', url):
            await status_message.edit_text(
                f"{EMOJI['error']} *Bu YouTube havolasi emas!*\n\n"
                f"Iltimos, to'g'ri YouTube havolasini yuboring.",
                parse_mode="Markdown"
            )
            return

        # Video ID'ni olish
        video_id = extract_video_id(url)
        if not video_id:
            await status_message.edit_text(
                f"{EMOJI['error']} *Video ID aniqlanmadi!*\n\n"
                f"Iltimos, to'g'ri YouTube havolasini yuboring.",
                parse_mode="Markdown"
            )
            return

        # YouTube API orqali video ma'lumotlarini olish
        video_info = await get_video_info(video_id)
        if not video_info:
            await status_message.edit_text(
                f"{EMOJI['error']} *Video topilmadi yoki xatolik yuz berdi!*\n\n"
                f"Iltimos, boshqa video havolasini yuboring.",
                parse_mode="Markdown"
            )
            return

        # Video haqida ma'lumot
        info_text = (
            f"*{EMOJI['youtube']} {video_info['title']}*\n\n"
            f"*{EMOJI['info']} Video ma'lumotlari:*\n"
            f"👤 *Yuklagan:* {video_info['channelTitle']}\n"
            f"⏱ *Davomiyligi:* {video_info['duration']}\n\n"
            f"{EMOJI['warning']} *Diqqat:* YouTube API cheklovlari tufayli, hozirda faqat video haqida ma'lumot olish mumkin.\n\n"
            f"{EMOJI['info']} Ushbu bot hozirda texnik muammolar tufayli fayllarni yuklab olmaydi. Iltimos keyinroq qayta urinib ko'ring yoki admin bilan bog'laning."
        )
        
        await status_message.edit_text(
            info_text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{EMOJI['youtube']} YouTube'da ko'rish", url=f"https://www.youtube.com/watch?v={video_id}")]
            ])
        )

    except Exception as e:
        logger.error(f"Download_video funksiyasida xatolik: {str(e)}")
        try:
            await update.message.reply_text(
                f"{EMOJI['error']} *Xatolik yuz berdi:* {str(e)}\n\n"
                f"Iltimos, qaytadan urinib ko'ring yoki boshqa havola yuboring.",
                parse_mode="Markdown"
            )
        except Exception:
            pass

if __name__ == '__main__':
    # audio_thumb.jpg faylini yaratish (agar mavjud bo'lmasa)
    if not os.path.exists("audio_thumb.jpg"):
        try:
            # Bo'sh fayl yaratish
            with open("audio_thumb.jpg", "w") as f:
                f.write("")
            print("audio_thumb.jpg fayli yaratildi.")
        except Exception as e:
            logger.error(f"audio_thumb.jpg faylini yaratishda xatolik: {str(e)}")
    
    # Botni ishga tushirish
    application = Application.builder().token(TOKEN).build()

    # Handler-lar
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(confirm_subscription, pattern="^confirm_subscribe$"))
    application.add_handler(CallbackQueryHandler(help_callback, pattern="^help$"))
    application.add_handler(MessageHandler(
        filters.Regex(r'^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$'),
        download_video
    ))
    
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        lambda update, context: update.message.reply_text(
            f"{EMOJI['error']} *Bu YouTube havolasi emas!*\n\n"
            f"Iltimos, to'g'ri YouTube havolasini yuboring. "
            f"Yordam uchun /help buyrug'ini ishlatishingiz mumkin.",
            parse_mode="Markdown"
        )
    ))

    # Webhook o'rnatish uchun PORT
    PORT = int(os.environ.get('PORT', '8443'))
    
    # Render serverida webhook rejimida ishlash
    RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL')
    if RENDER_EXTERNAL_URL:
        print(f"Webhook rejimida ishga tushirilmoqda: {RENDER_EXTERNAL_URL}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{RENDER_EXTERNAL_URL}/{TOKEN}"
        )
    else:
        # Mahalliy rivojlantirish uchun polling
        print(f"{EMOJI['success']} Bot polling rejimida ishga tushdi!")
        application.run_polling()
