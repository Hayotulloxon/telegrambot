#!/usr/bin/env bash
# FFmpeg va boshqa kerakli paketlarni o'rnatish
apt-get update -qq && apt-get -y install ffmpeg

# SSL tekshiruvini o'chirish uchun Python muhitini o'zgartirish
echo "export PYTHONHTTPSVERIFY=0" >> ~/.bashrc
echo "export PYTHONHTTPSVERIFY=0" >> ~/.profile

# yt-dlp-ni so'nggi versiyaga yangilash
pip install --upgrade yt-dlp
