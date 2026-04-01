import time
import re
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from monitor.models import ScrapedItem, WatchTask
from monitor.scraper import scrape_ebay # 确保这是你之前的爬虫函数

class Command(BaseCommand):
    help = '监控 eBay 上的 iPhone 并发送邮件预警'

    from monitor.models import ScrapedItem, WatchTask 
# ... 其他导入保持不变 ...

class Command(BaseCommand):
    def handle(self, *args, **options):
        # 1. 只获取“激活中”的任务
        tasks = WatchTask.objects.filter(is_active=True)
        
        for task in tasks:
            print(f"🔍 正在执行任务: {task.keywords} (限价: ${task.max_price})")
            
            # 调用爬虫，传入当前任务的关键词和限价
            items = scrape_ebay(task.keywords, float(task.max_price))
            
            new_items_found = []
            for item in items:
                title = item['title']
                title_lower = title.lower()
                kw_lower = task.keywords.lower()

                # --- 🛑 强效过滤器开始 ---
                # --- 🛑 关键点：在这里初始化变量 ---
                found_noise = False
                
                # A. 关键词包含校验：如果标题里连监控词都没有，直接扔掉
                # 例如：搜 iPhone 13 结果出来个 Samsung，这行就会把它拦截
                if kw_lower not in title_lower:
                    found_noise = True # 没搜到关键词也算作噪音/无效数据
                
                # B. 噪音排除：排除常见的“非手机”和“竞争对手”干扰词
                noise_words = ['samsung', 'google', 'pixel', 'nokia', 'case', 'box only', 'parts']
                # 如果监控词本身不是 samsung，但标题里有 samsung，就过滤掉
                if any(noise in title_lower for noise in noise_words) and (noise not in kw_lower):
                    found_noise = True
                    break # 只要发现一个干扰词就够了

                if found_noise:
                    print(f"⏩ 过滤噪音: {title[:30]}...")
                    continue
                # --- 🛑 强效过滤器结束 ---

                # 3. 查重并保存
                if not ScrapedItem.objects.filter(url=item['link']).exists():
                    ScrapedItem.objects.create(
                        task=task,
                        title=title,
                        price=item['price'],
                        url=item['link']
                    )
                    new_items_found.append(item)
                    print(f"✨ 发现符合要求的新货: {title[:30]}...")

            # 发送该任务的预警邮件
            if new_items_found:
                self.send_alert_email(new_items_found, task)
            else:
                print("😴 没有发现新货，继续监控中...")

    def send_alert_email(self, items_list, task):
        subject = f"🔥 发现 {len(items_list)} 个新上架的 {task.keywords}！"
        
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