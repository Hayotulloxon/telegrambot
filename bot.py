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
        f"3. Sizga kerakli sifatni tanlang\n"
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
        f"3. Sizga kerakli sifatni tanlang\n"
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
        
        # Shorts havolasini standart formatga o'tkazish
        if 'shorts' in url:
            try:
                video_id = re.search(r'(?<=shorts/)[^/?]+', url).group()
                url = f'https://www.youtube.com/watch?v={video_id}'
            except (AttributeError, Exception) as e:
                logger.error(f"Shorts havolasini o'zgartirishda xatolik: {str(e)}")
                await status_message.edit_text(
                    f"{EMOJI['error']} *Shorts havolasini qayta ishlashda xatolik yuz berdi!*",
                    parse_mode="Markdown"
                )
                return

        # YouTube havolasi formatini tekshirish
        if not re.match(r'^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$', url):
            await status_message.edit_text(
                f"{EMOJI['error']} *Bu YouTube havolasi emas!*\n\n"
                f"Iltimos, to'g'ri YouTube havolasini yuboring.",
                parse_mode="Markdown"
            )
            return

        # Videoni tahlil qilish - YouTube CAPTCHA muammosiga qarshi yechimlar
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'no_check_certificate': True,  # SSL sertifikatini tekshirmaslik
            'ignoreerrors': True,  # Xatoliklarni e'tiborsiz qoldirish
            'nocheckcertificate': True,  # SSL sertifikatini tekshirmaslik
            'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,  # Cookies fayli mavjud bo'lsa
            'skip_download': True,  # Faqat ma'lumotlarni olish, yuklash emas
            'extractor_args': {
                'youtube': {
                    'skip': ['dash', 'hls'],  # Maxsus formatlarni o'tkazib yuborish
                    'player_client': ['android', 'web']  # Turli mijozlarni sinab ko'rish
                }
            },
            'socket_timeout': 30  # Timeout muddatini oshirish
        }
        
        try:
            # YouTube API-ga so'rov yuborish
            logger.info(f"Video ma'lumotlarini olish boshlandi: {url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])
                title = info.get('title', 'Video')
                duration = info.get('duration')
                uploader = info.get('uploader', 'Unknown')
                thumbnail = info.get('thumbnail')
                
            logger.info(f"Video ma'lumotlari muvaffaqiyatli olindi: {title}")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Video ma'lumotlarini olishda xatolik: {error_msg}")
            
            # YouTube captcha xatoligini tekshirish
            if "Sign in to confirm you're not a bot" in error_msg:
                await status_message.edit_text(
                    f"{EMOJI['error']} *YouTube captcha xatoligi yuz berdi!*\n\n"
                    f"Afsuski, YouTube botni bloklagan ko'rinadi. Admin bilan bog'laning.",
                    parse_mode="Markdown"
                )
                return
            
            await status_message.edit_text(
                f"{EMOJI['error']} *Video topilmadi yoki xatolik yuz berdi!*\n\n"
                f"Xatolik: {error_msg}",
                parse_mode="Markdown"
            )
            return

        if not formats:
            await status_message.edit_text(
                f"{EMOJI['error']} *Videoni yuklab bo'lmadi!*\n\n"
                f"Bu video uchun formatlar topilmadi.",
                parse_mode="Markdown"
            )
            return

        # Formatlarni audio va video bo'yicha ajratish
        audio_formats = []
        video_formats = []
        
        for fmt in formats:
            vcodec = fmt.get('vcodec', 'none')
            acodec = fmt.get('acodec', 'none')
            
            if vcodec == 'none' and acodec != 'none':  # Faqat audio
                audio_formats.append(fmt)
            elif acodec != 'none' and vcodec != 'none':  # Video + audio
                video_formats.append(fmt)

        # Formatlar mavjudligini tekshirish va saqlash
        if not audio_formats and not video_formats:
            await status_message.edit_text(
                f"{EMOJI['error']} *Ushbu videoda mavjud formatlar topilmadi!*",
                parse_mode="Markdown"
            )
            return

        # Video haqida ma'lumot
        duration_str = "Noma'lum"
        if duration:
            minutes, seconds = divmod(duration, 60)
            duration_str = f"{minutes}:{seconds:02d}" if minutes < 60 else f"{minutes//60}:{minutes%60:02d}:{seconds:02d}"
        
        info_text = (
            f"*{EMOJI['youtube']} {title}*\n\n"
            f"*{EMOJI['info']} Video ma'lumotlari:*\n"
            f"👤 *Yuklagan:* {uploader}\n"
            f"⏱ *Davomiyligi:* {duration_str}\n\n"
            f"{EMOJI['download']} *Yuklash formatini tanlang:*"
        )
        
        # Tugmalar yaratish
        keyboard = []
        if audio_formats:
            keyboard.append([InlineKeyboardButton(f"{EMOJI['audio']} Audio", callback_data="media_audio")])
        if video_formats:
            keyboard.append([InlineKeyboardButton(f"{EMOJI['video']} Video", callback_data="media_video")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Ma'lumotlarni yangilash
        await status_message.edit_text(
            info_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        # Ma'lumotlarni saqlash
        context.user_data['audio_formats'] = audio_formats
        context.user_data['video_formats'] = video_formats
        context.user_data['title'] = title
        context.user_data['url'] = url
        context.user_data['status_message'] = status_message

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

@restricted
async def handle_media_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Media turini tanlash"""
    try:
        query = update.callback_query
        await query.answer()
        
        media_type = query.data.split('_')[1]
        formats = context.user_data.get(f'{media_type}_formats', [])
        
        if not formats:
            await query.edit_message_text(
                f"{EMOJI['error']} *{media_type.capitalize()} formatlar mavjud emas!*",
                parse_mode="Markdown"
            )
            return

        # Formatlarni sifat bo'yicha saralash
        if media_type == 'audio':
            # Audio formatlarni bit_rate bo'yicha saralash
            formats.sort(key=lambda x: x.get('abr', 0) if x.get('abr') else 0, reverse=True)
        else:
            # Video formatlarni height bo'yicha saralash
            formats.sort(key=lambda x: x.get('height', 0) if x.get('height') else 0, reverse=True)

        # Formatlarni tayyorlash
        resolutions = []
        format_map = {}
        
        for fmt in formats:
            # Formatga qarab etiketni tayyorlash
            if media_type == 'audio':
                abr = fmt.get('abr', 0)
                filesize = fmt.get('filesize', 0) or 0
                filesize_mb = round(filesize / (1024 * 1024), 2) if filesize else "Noma'lum"
                ext = 'mp3'  # Audio uchun mp3 formatida yuklash
                
                if abr:
                    label = f"{abr}kbps ({ext}, {filesize_mb} MB)"
                else:
                    label = f"Standart sifat ({ext}, {filesize_mb} MB)"
                    
                label = f"{EMOJI['audio']} {label}"
            else:
                height = fmt.get('height', 0)
                width = fmt.get('width', 0)
                ext = 'mp4'  # Video uchun mp4 formatida yuklash
                filesize = fmt.get('filesize', 0) or 0
                filesize_mb = round(filesize / (1024 * 1024), 2) if filesize else "Noma'lum"
                
                if height and width:
                    label = f"{width}x{height} ({ext}, {filesize_mb} MB)"
                else:
                    label = f"Standart sifat ({ext}, {filesize_mb} MB)"
                    
                label = f"{EMOJI['video']} {label}"

            resolutions.append(label)
            format_map[label] = fmt['url']

        # Ekranni formatlarga bo'lish
        keyboard = []
        chunk_size = 2
        for i in range(0, len(resolutions), chunk_size):
            row = []
            for res in resolutions[i:i+chunk_size]:
                row.append(InlineKeyboardButton(res, callback_data=f"format_{res}"))
            keyboard.append(row)
        
        # Orqaga qaytish tugmasi
        keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_main")])
        
        title = context.user_data.get('title', 'Video')
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"*{EMOJI['youtube']} {title}*\n\n"
            f"{EMOJI['quality']} *{media_type.capitalize()} formatlardan birini tanlang:*",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

        # Ma'lumotlarni saqlash
        context.user_data['format_map'] = format_map
        context.user_data['media_type'] = media_type

    except Exception as e:
        logger.error(f"Handle_media_type funksiyasida xatolik: {str(e)}")
        await query.edit_message_text(
            f"{EMOJI['error']} *Xatolik yuz berdi:* {str(e)}\n\n"
            f"Iltimos, qaytadan urinib ko'ring.",
            parse_mode="Markdown"
        )

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Asosiy menyuga qaytish"""
    query = update.callback_query
    await query.answer()
    
    title = context.user_data.get('title', 'Video')
    audio_formats = context.user_data.get('audio_formats', [])
    video_formats = context.user_data.get('video_formats', [])
    
    keyboard = []
    if audio_formats:
        keyboard.append([InlineKeyboardButton(f"{EMOJI['audio']} Audio", callback_data="media_audio")])
    if video_formats:
        keyboard.append([InlineKeyboardButton(f"{EMOJI['video']} Video", callback_data="media_video")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"*{EMOJI['youtube']} {title}*\n\n"
        f"{EMOJI['download']} *Yuklash formatini tanlang:*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

@restricted
async def handle_quality_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sifat tanlanishi"""
    try:
        query = update.callback_query
        await query.answer()
        
        if query.data == "back_to_main":
            return await back_to_main(update, context)
        
        if not query.data.startswith("format_"):
            return
            
        selected_label = query.data[7:]  # "format_" prefiksini olib tashlash
        format_map = context.user_data.get('format_map', {})
        media_type = context.user_data.get('media_type')
        original_title = context.user_data.get('title', 'Video')
        url = context.user_data.get('url')

        # Fayl nomini tozalash
        safe_title = re.sub(r'[^\w\-_.() ]', '_', original_title)
        safe_title = safe_title[:100]  # Uzun nomlarni qisqartirish

        if selected_label not in format_map:
            await query.edit_message_text(
                f"{EMOJI['error']} *Tanlangan format topilmadi!*",
                parse_mode="Markdown"
            )
            return

        # Yuklashni boshlash
        await query.edit_message_text(
            f"{EMOJI['loading']} *{media_type.capitalize()} yuklanmoqda...*\n\n"
            f"Format: {selected_label}\n\n"
            f"Bu jarayon bir necha daqiqa vaqt olishi mumkin. Iltimos kuting...",
            parse_mode="Markdown"
        )

        # Yuklash sozlamalari
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{safe_title}_{current_time}"
        
        # YouTube CAPTCHA muammosiga qarshi yechimlar
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'outtmpl': f'{output_filename}.%(ext)s',
            'postprocessors': [],
            'no_check_certificate': True,  # SSL sertifikatini tekshirmaslik
            'ignoreerrors': True,  # Xatoliklarni e'tiborsiz qoldirish
            'nocheckcertificate': True,  # SSL sertifikatini tekshirmaslik
            'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,  # Cookies fayli mavjud bo'lsa
            'socket_timeout': 30,  # Timeout muddatini oshirish
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']  # Turli mijozlarni sinab ko'rish
                }
            }
        }

        # Media turiga qarab sozlamalar
        if media_type == 'audio':
            ydl_opts.update({
                'format': 'bestaudio',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
            final_ext = 'mp3'
        else:
            ydl_opts.update({
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
            })
            final_ext = 'mp4'

        # Video yoki audio sifatida yuklash
        try:
            logger.info(f"Yuklash boshlandi: {url}, format: {media_type}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            logger.info(f"Yuklash tugadi: {output_filename}")
        except Exception as download_err:
            error_msg = str(download_err)
            logger.error(f"Yuklashda xatolik: {error_msg}")
            
            # YouTube captcha xatoligini tekshirish
            if "Sign in to confirm you're not a bot" in error_msg:
                await query.edit_message_text(
                    f"{EMOJI['error']} *YouTube captcha xatoligi yuz berdi!*\n\n"
                    f"Afsuski, YouTube botni bloklagan ko'rinadi. Admin bilan bog'laning.",
                    parse_mode="Markdown"
                )
            else:
                await query.edit_message_text(
                    f"{EMOJI['error']} *Yuklashda xatolik:* {error_msg}",
                    parse_mode="Markdown"
                )
            return

        # Tayyor fayl nomini aniqlash
        final_filename = f"{output_filename}.{final_ext}"
        
        # Fayl mavjudligini tekshirish
        if not os.path.exists(final_filename):
            await query.edit_message_text(
                f"{EMOJI['error']} *Fayl topilmadi!* Yuklash jarayonida xatolik.",
                parse_mode="Markdown"
            )
            return

        # Foydalanuvchi statistikasini yangilash
        user_id = query.from_user.id
        if user_id in user_stats:
            user_stats[user_id]["downloads"] += 1

        # Faylni yuborish
        try:
            await query.edit_message_text(
                f"{EMOJI['loading']} *Fayl yuborilmoqda...*",
                parse_mode="Markdown"
            )
            
            caption = f"{EMOJI['youtube']} *{original_title}*\n"
            caption += f"@YouTubeDownloaderUzBot orqali yuklandi"
            
            if media_type == 'audio':
                await context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=open(final_filename, 'rb'),
                    thumb=open("audio_thumb.jpg", 'rb') if os.path.exists("audio_thumb.jpg") else None,
                    title=original_title,
                    caption=caption,
                    parse_mode="Markdown",
                    filename=f"{safe_title}.mp3"
                )
            else:
                await context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=open(final_filename, 'rb'),
                    caption=caption,
                    parse_mode="Markdown",
                    filename=f"{safe_title}.mp4",
                    width=1280,
                    height=720
                )
                
            # Xabarni o'chirish
            await query.delete_message()
            
            # Foydalanuvchiga qo'shimcha xabar yuborish
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"{EMOJI['success']} *Yuklash muvaffaqiyatli yakunlandi!*\n\n"
                     f"Boshqa video yuklash uchun yangi havola yuboring.",
                parse_mode="Markdown"
            )
            
        except Exception as send_err:
            logger.error(f"Yuborishda xatolik: {str(send_err)}")
            await query.edit_message_text(
                f"{EMOJI['error']} *Faylni yuborishda xatolik!* {str(send_err)}",
                parse_mode="Markdown"
            )
        finally:
            # Tozalash
            if os.path.exists(final_filename):
                os.remove(final_filename)

    except Exception as e:
        logger.error(f"Handle_quality_choice funksiyasida xatolik: {str(e)}")
        try:
            await query.edit_message_text(
                f"{EMOJI['error']} *Xatolik:* {str(e)}\n\n"
                f"Iltimos, qaytadan urinib ko'ring.",
                parse_mode="Markdown"
            )
        except Exception:
            pass

# Asosiy funksiya yo'q - Render uchun to'g'ridan-to'g'ri main blokdan foydalanish

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
    application.add_handler(CallbackQueryHandler(back_to_main, pattern="^back_to_main$"))
    application.add_handler(CallbackQueryHandler(handle_media_type, pattern="^media_"))
    application.add_handler(CallbackQueryHandler(handle_quality_choice))
    
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
