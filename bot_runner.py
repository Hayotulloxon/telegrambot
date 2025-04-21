#!/usr/bin/env python3
import os
import sys
import ssl

# SSL tekshirishni o'chirish
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['PYTHONHTTPSVERIFY'] = '0'

# Bot skriptini ishga tushirish
os.system('python bot.py')
