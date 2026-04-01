import time
import re
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from monitor.models import ScrapedItem, WatchTask
from monitor.scraper import scrape_ebay # 确保这是你之前的爬虫函数

class Command(BaseCommand):
    help = '监控 eBay 上的 iPhone 并发送邮件预警'

    def handle(self, *args, **options):
        print("--- 市场扫描开始 ---")
        
        # 1. 调用你之前的爬虫函数
        # 假设返回格式为 [{'title': '...', 'price': 123.0, 'link': '...'}]
        items = scrape_ebay("iPhone 13", 2000.00)
        
        new_items_found = []
        # 定义要排除的噪音关键词
        exclude_keywords = ['Category', 'Samsung', 'Nokia', 'Motorola', 'Google', 'Price']

        for item in items:
            # 过滤噪音逻辑保持不变...
            
            # 2. 这里的查询和创建要匹配你的模型字段 (url 而不是 link)
            if not ScrapedItem.objects.filter(url=item['link']).exists():
                # 获取一个任务关联（因为你的 ScrapedItem 必须关联一个 WatchTask）
                # 这里我们暂且取第一个 iPhone 13 的任务，如果没有就创建一个
                task, _ = WatchTask.objects.get_or_create(
                    keywords="iPhone 13", 
                    defaults={'max_price': 2000, 'user_id': 1} # 假设 ID 为 1 的是你的管理员账号
                )

                # 3. 存入数据库 (注意字段名对应：url=item['link'])
                ScrapedItem.objects.create(
                    task=task,
                    title=item['title'],
                    price=item['price'],
                    url=item['link']  # 你的模型里叫 url
                )
                new_items_found.append(item)
                print(f"✨ 发现新货: {item['title'][:30]}... ${item['price']}")

        # 3. 如果有新发现，发邮件汇总
        if new_items_found:
            self.send_alert_email(new_items_found)
        else:
            print("📭 本次扫描没有发现新上架的商品。")

    def send_alert_email(self, items_list):
        subject = f"🔥 发现 {len(items_list)} 个新上架的 iPhone 13！"
        
        # 构造邮件正文
        body = "老板，这些是刚抓到的新货，看准了赶紧下手：\n"
        body += "="*40 + "\n\n"
        for i in items_list:
            body += f"💰 价格: ${i['price']}\n"
            body += f"📱 标题: {i['title']}\n"
            body += f"🔗 链接: {i['link']}\n"
            body += "-"*40 + "\n"
        
        try:
            send_mail(
                subject,
                body,
                None, # 自动使用 settings.py 里的 EMAIL_HOST_USER
                ['zzj20050510@hotmail.com'], # 你的收件邮箱
                fail_silently=False,
            )
            print(f"📢 预警邮件已发送至个人邮箱！")
        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")