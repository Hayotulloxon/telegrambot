from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ContextTypes
)
import yt_dlp
import logging
import re
import os
import asyncio
from datetime import datetime

# Bot sozlamalari
TOKEN = '7987802742:AAEVZTrn1_8w0l601bLMn4O-ONiw4w9PWNA'
YOUTUBE_CHANNEL_URL = 'https://www.youtube.com/@Sonic_edits-c4e'

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

# O'zgaruvchilar
DOWNLOADS_FOLDER = "downloads"
if not os.path.exists(DOWNLOADS_FOLDER):
    os.makedirs(DOWNLOADS_FOLDER)

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
        f"3. Yuklab olish tugagach, fayl avtomatik ravishda yuboriladi\n\n"
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
        f"3. Yuklab olish tugagach, fayl avtomatik ravishda yuboriladi\n\n"
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

        # Video haqida ma'lumot olish
        try:
            # YT-DLP sozlamalari
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'ignoreerrors': True,
                'extract_flat': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
            if not info:
                await status_message.edit_text(
                    f"{EMOJI['error']} *Video topilmadi!*\n\n"
                    f"Iltimos, boshqa YouTube havolasini yuboring.",
                    parse_mode="Markdown"
                )
                return
                
            title = info.get('title', 'Unknown Title')
            uploader = info.get('uploader', 'Unknown')
            
            # Format tanlash uchun tugmalar
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{EMOJI['audio']} Audio (MP3)", callback_data=f"dl_audio_{url}")],
                [InlineKeyboardButton(f"{EMOJI['video']} Video (MP4)", callback_data=f"dl_video_{url}")]
            ])
            
            await status_message.edit_text(
                f"{EMOJI['youtube']} *{title}*\n"
                f"👤 *Yuklagan:* {uploader}\n\n"
                f"{EMOJI['download']} *Yuklab olish formatini tanlang:*",
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Video ma'lumotlarini olishda xatolik: {str(e)}")
            await status_message.edit_text(
                f"{EMOJI['error']} *Video ma'lumotlarini olishda xatolik:*\n{str(e)}\n\n"
                f"Iltimos, boshqa YouTube havolasini yuboring.",
                parse_mode="Markdown"
            )
            return

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

async def process_download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Download formatini tanlash tugmasi bosilganda"""
    query = update.callback_query
    await query.answer()
    
    # Callback data-ni tahlil qilish
    data = query.data.split('_')
    if len(data) < 3:
        await query.edit_message_text(
            f"{EMOJI['error']} *Noto'g'ri format!*",
            parse_mode="Markdown"
        )
        return
        
    format_type = data[1]  # audio yoki video
    url = '_'.join(data[2:])  # URL (underscore bilan bo'lingan bo'lishi mumkin)
    
    # Yuklanayotganini xabar berish
    await query.edit_message_text(
        f"{EMOJI['loading']} *{format_type.capitalize()} yuklanmoqda...*\n\n"
        f"Bu jarayon bir necha daqiqa vaqt olishi mumkin. Iltimos kuting...",
        parse_mode="Markdown"
    )
    
    try:
        # Vaqt belgi
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Fayl nomini tozalash
        safe_filename = f"youtube_{timestamp}"
        output_path = os.path.join(DOWNLOADS_FOLDER, safe_filename)
        
        if format_type == "audio":
            # Audio yuklab olish sozlamalari
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{output_path}.%(ext)s',
                'nocheckcertificate': True,
                'ignoreerrors': True,
                'prefer_ffmpeg': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Unknown')
                
            # MP3 faylini topish
            audio_file = f"{output_path}.mp3"
            
            if not os.path.exists(audio_file):
                await query.edit_message_text(
                    f"{EMOJI['error']} *Audio faylni yuklab olishda xatolik!*\n\n"
                    f"Fayl topilmadi.",
                    parse_mode="Markdown"
                )
                return
                
            # Audiofaylni yuborish
            caption = f"{EMOJI['youtube']} *{title}*\n@YouTubeDownloaderUzBot orqali yuklandi"
            await context.bot.send_audio(
                chat_id=query.message.chat_id,
                audio=open(audio_file, 'rb'),
                caption=caption,
                parse_mode="Markdown",
                title=title
            )
            
            # Faylni o'chirish
            os.remove(audio_file)
            
            # Muvaffaqiyatli xabar
            await query.edit_message_text(
                f"{EMOJI['success']} *Audio yuklab olindi!*\n\n"
                f"*{title}*\n\n"
                f"Boshqa video yuklab olish uchun yangi YouTube havolasini yuboring.",
                parse_mode="Markdown"
            )
            
        elif format_type == "video":
            # Video yuklab olish sozlamalari
            ydl_opts = {
                'format': 'best',
                'outtmpl': f'{output_path}.%(ext)s',
                'nocheckcertificate': True,
                'ignoreerrors': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Unknown')
                
            # Faylni topish
            video_files = [f for f in os.listdir(DOWNLOADS_FOLDER) if f.startswith(os.path.basename(output_path))]
            if not video_files:
                await query.edit_message_text(
                    f"{EMOJI['error']} *Video faylni yuklab olishda xatolik!*\n\n"
                    f"Fayl topilmadi.",
                    parse_mode="Markdown"
                )
                return
                
            video_file = os.path.join(DOWNLOADS_FOLDER, video_files[0])
            
            # Videofaylni yuborish
            caption = f"{EMOJI['youtube']} *{title}*\n@YouTubeDownloaderUzBot orqali yuklandi"
            await context.bot.send_video(
                chat_id=query.message.chat_id,
                video=open(video_file, 'rb'),
                caption=caption,
                parse_mode="Markdown",
                supports_streaming=True
            )
            
            # Faylni o'chirish
            os.remove(video_file)
            
            # Muvaffaqiyatli xabar
            await query.edit_message_text(
                f"{EMOJI['success']} *Video yuklab olindi!*\n\n"
                f"*{title}*\n\n"
                f"Boshqa video yuklab olish uchun yangi YouTube havolasini yuboring.",
                parse_mode="Markdown"
            )
            
        else:
            await query.edit_message_text(
                f"{EMOJI['error']} *Noto'g'ri format turi!*",
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"Process_download funksiyasida xatolik: {str(e)}")
        await query.edit_message_text(
            f"{EMOJI['error']} *Yuklab olishda xatolik:* {str(e)}\n\n"
            f"Iltimos, boshqa havola bilan urinib ko'ring yoki keyinroq qayta harakat qiling.",
            parse_mode="Markdown"
        )

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
    application.add_handler(CallbackQueryHandler(process_download, pattern="^dl_"))
    
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
