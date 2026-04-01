import os
import datetime
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from monitor.models import ScrapedItem, WatchTask 
from monitor.scraper import scrape_ebay  # 确保你的爬虫函数路径正确

