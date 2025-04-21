#!/usr/bin/env bash
# FFmpeg va boshqa kerakli paketlarni o'rnatish
apt-get update -qq && apt-get -y install ffmpeg

# environment variables (SSL sertifikat tekshiruvini o'chirish)
export PYTHONHTTPSVERIFY=0
echo "export PYTHONHTTPSVERIFY=0" >> ~/.bashrc

# youtube-dl-ni o'rnatish va yangilash
python -m pip install --upgrade youtube-dl
pip install --upgrade yt-dlp

# youtube-dl uchun config faylini yaratish
mkdir -p ~/.config/youtube-dl/
echo "--no-check-certificate" > ~/.config/youtube-dl/config
echo "--no-warnings" >> ~/.config/youtube-dl/config
