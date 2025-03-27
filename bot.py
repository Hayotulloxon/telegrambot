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

# Bot sozlamalari
TOKEN = '7987802742:AAEVZTrn1_8w0l601bLMn4O-ONiw4w9PWNA'
YOUTUBE_CHANNEL_URL = 'https://www.youtube.com/@Sonic_edits-c4e'

# Loglash tizimi
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

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
            await update.message.reply_text(
                "Botdan foydalanish uchun avval YouTube kanalimizga obuna bo'ling!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(" YouTube kanaliga obuna bo'lish ", url=YOUTUBE_CHANNEL_URL),
                    InlineKeyboardButton("✅ Obunani tasdiqlash", callback_data="confirm_subscribe")
                ]])
            )
            return
    return wrapped

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    subscribed = await check_subscription(context, user_id)
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(" YouTube kanaliga obuna bo'lish ", url=YOUTUBE_CHANNEL_URL),
            InlineKeyboardButton("✅ Obunani tasdiqlash", callback_data="confirm_subscribe")
        ]
    ])
    
    if not subscribed:
        await update.message.reply_text(
            "Botdan foydalanish uchun avval YouTube kanalimizga obuna bo'ling!",
            reply_markup=keyboard
        )
    else:
        await update.message.reply_text('Salom! YouTube havolasini yuboring.')

async def confirm_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    context.user_data[f'subscribed_{user_id}'] = True
    
    await query.edit_message_text("✅ Obuna muvaffaqiyatli tasdiqlandi!")
    await query.message.reply_text(
        "endi YouTube havolasini yuborishingiz mumkin.\n\n"
        "Misol: https://youtu.be/abcd1234"
    )

@restricted
async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        url = update.message.text
        
        # Shorts havolasini standart formatga o'tkazish
        if 'shorts' in url:
            video_id = re.search(r'(?<=shorts/)[^/?]+', url).group()
            url = f'https://www.youtube.com/watch?v={video_id}'

        # YouTube havolasi formatini tekshirish
        if not re.match(r'^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$', url):
            await update.message.reply_text("❌ Bu YouTube havolasi emas!")
            return

        # Videoni tahlil qilish
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])
            except Exception as e:
                await update.message.reply_text("❌ Video topilmadi yoki xatolik yuz berdi!")
                return

        if not formats:
            await update.message.reply_text("❌ Videoni yuklab bo'lmadi!")
            return

        # Formatlarni audio va video bo'yicha ajratish
        audio_formats = []
        video_formats = []
        for fmt in formats:
            vcodec = fmt.get('vcodec', 'none')
            acodec = fmt.get('acodec', 'none')
            
            if vcodec == 'none':  # Faqat audio
                audio_formats.append(fmt)
            elif acodec != 'none':  # Video + audio
                video_formats.append(fmt)

        # Tugmalar yaratish
        keyboard = []
        if audio_formats:
            keyboard.append([InlineKeyboardButton("🎧 Audio", callback_data="media_audio")])
        if video_formats:
            keyboard.append([InlineKeyboardButton("📹 Video", callback_data="media_video")])
        
        if not keyboard:
            await update.message.reply_text("❌ Ushbu videoda mavjud formatlar topilmadi!")
            return

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("🎧 Audio yoki 📹 Video tanlang:", reply_markup=reply_markup)

        # Ma'lumotlarni saqlash
        context.user_data['audio_formats'] = audio_formats
        context.user_data['video_formats'] = video_formats
        context.user_data['title'] = info.get('title', 'Video')
        context.user_data['url'] = url

    except Exception as e:
        logging.error(f"Xatolik: {str(e)}")
        await update.message.reply_text(f"❌ Xatolik yuz berdi: {str(e)}")

@restricted
async def handle_media_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        query = update.callback_query
        await query.answer()
        
        media_type = query.data.split('_')[1]
        formats = context.user_data.get(f'{media_type}_formats', [])
        
        if not formats:
            await query.edit_message_text(f"❌ {media_type.capitalize()} formatlar mavjud emas!")
            return

        # Formatlarni tayyorlash
        resolutions = []
        format_map = {}
        for fmt in formats:
            resolution = fmt.get('resolution', 'Noma\'lum')
            ext = fmt.get('ext', 'mp4')
            filesize = fmt.get('filesize', 0) or 0
            filesize_mb = round(filesize / (1024 * 1024), 2) if filesize else "Noma'lum"
            vcodec = fmt.get('vcodec', 'none')
            acodec = fmt.get('acodec', 'none')

            label = f"{resolution} ({ext}, {filesize_mb} MB)"
            if media_type == 'audio':
                label += " [Audio]"
            else:
                label += " [Video+Audio]"

            resolutions.append(label)
            format_map[label] = fmt['url']

        # Tugmalar yaratish
        keyboard = []
        for res in resolutions:
            keyboard.append([InlineKeyboardButton(res, callback_data=res)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"🔍 {media_type.capitalize()} formatlardan birini tanlang:",
            reply_markup=reply_markup
        )

        # Ma'lumotlarni saqlash
        context.user_data['format_map'] = format_map
        context.user_data['media_type'] = media_type

    except Exception as e:
        logging.error(f"Xatolik: {str(e)}")
        await query.edit_message_text(f"❌ Xatolik yuz berdi: {str(e)}")

@restricted
async def handle_quality_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        query = update.callback_query
        await query.answer()

        selected_label = query.data
        format_map = context.user_data.get('format_map', {})
        media_type = context.user_data.get('media_type')
        original_title = context.user_data.get('title', 'Video')
        url = context.user_data.get('url')

        # Fayl nomini tozalash
        safe_title = re.sub(r'[^\w\-_.() ]', '_', original_title)

        if selected_label not in format_map:
            await query.edit_message_text("❌ Tanlangan format topilmadi!")
            return

        video_url = format_map[selected_label]

        # Yuklashni boshlash
        message = await query.edit_message_text("⏳ Format yuklanmoqda...")

        # Yuklash sozlamalari
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'outtmpl': f'{safe_title}.%(ext)s',
            'postprocessors': [],
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
        else:
            ydl_opts.update({
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
            })

        # Video yoki audio sifatida yuklash
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            filename = ydl.prepare_filename(info)
            ydl.download([url])

            # Audio uchun fayl nomini aniqlash
            if media_type == 'audio':
                base_name, _ = os.path.splitext(filename)
                audio_filename = f"{base_name}.mp3"
            else:
                audio_filename = None

        # Faylni yuborish
        try:
            if media_type == 'audio':
                await context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=open(audio_filename, 'rb'),
                    filename=f"{safe_title}.mp3",
                    caption=f"🎧 {original_title}\n"
                )
            else:
                await context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=open(filename, 'rb'),
                    filename=f"{safe_title}.mp4",
                    caption=f"📹 {original_title}\n"
                )
        except Exception as send_err:
            logging.error(f"Yuborishda xatolik: {send_err}")
            await query.edit_message_text("❌ Faylni yuborishda xatolik yuz berdi!")
            raise send_err
        finally:
            # Tozalash
            await message.delete()
            if os.path.exists(filename):
                os.remove(filename)
            if audio_filename and os.path.exists(audio_filename):
                os.remove(audio_filename)

    except Exception as e:
        logging.error(f"Xatolik: {str(e)}")
        await query.edit_message_text(f"❌ Yuklashda xatolik: {str(e)}")
        # Xatolik yuz berganda fayllarni tozalash
        if 'filename' in locals():
            if os.path.exists(filename):
                os.remove(filename)
        if 'audio_filename' in locals():
            if audio_filename and os.path.exists(audio_filename):
                os.remove(audio_filename)

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    # Handler-lar
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(confirm_subscription, pattern="^confirm_subscribe$"))
    application.add_handler(MessageHandler(
        filters.Regex(r'^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$'),
        download_video
    ))
    application.add_handler(CallbackQueryHandler(handle_media_type, pattern='^media_'))
    application.add_handler(CallbackQueryHandler(handle_quality_choice))

    application.run_polling()

if __name__ == '__main__':
    main()
