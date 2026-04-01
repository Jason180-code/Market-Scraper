import os
import datetime
from django import tasks
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from monitor.models import ScrapedItem, WatchTask 
from monitor.scraper import scrape_ebay  # 确保你的爬虫函数路径正确

class Command(BaseCommand):
    help = '监控 eBay 任务并发送邮件预警'

    def handle(self, *args, **options):
        print(f"--- 市场扫描开始 ({datetime.datetime.now().strftime('%H:%M:%S')}) ---")
        
        # 1. 获取所有激活的任务
        tasks = WatchTask.objects.filter(is_active=True)

        noise_words = [
            'case', 'cover', 'glass', 'screen protector', 'tempered', 
            'film', 'lens', 'dummy', 'box only', 'parts', 'samsung', 'google'
        ]

        if not tasks.exists():
            print("📭 没有激活的监控任务，请在 Admin 后台添加。")
            return

    for task in tasks:
            print(f"🔍 执行任务: [{task.keywords}] | 限价: ${task.min_price} - ${task.max_price}")
            
            items = scrape_ebay(task.keywords, float(task.max_price))
            new_items_found = []
            kw_lower = task.keywords.lower()
            
            # --- 核心循环开始 ---
            for item in items:
                title = item['title']
                title_lower = title.lower()
                price = float(item['price'])

                # --- 🛑 过滤器第一关：黑名单 (对齐到这里) ---
                is_invalid = False
                for noise in noise_words:
                    if noise in title_lower:
                        is_invalid = True
                        break
                
                if is_invalid: 
                    continue

                # --- 🛑 过滤器第二关：价格区间 (对齐到这里) ---
                if price < float(task.min_price):
                    continue 
                    
                if price > float(task.max_price):
                    continue

                # --- 🛑 过滤器第三关：真机特征 (对齐到这里) ---
                if task.must_contain:
                    required_words = [w.strip().lower() for w in task.must_contain.split(',')]
                    if not any(word in title_lower for word in required_words):
                        continue

                # --- ✨ 只有通过所有关卡的，才是真正的“好货” ---
                print(f"💎 成功通过过滤: {title[:40]}... ${price}")

                # --- ✅ 3. 查重与保存 (对齐到这里) ---
                if not ScrapedItem.objects.filter(url=item['link']).exists():
                    try:
                        ScrapedItem.objects.create(
                            task=task,
                            title=title,
                            price=price, 
                            url=item['link']
                        )
                        new_items_found.append(item)
                        print(f"✨ 发现并存入数据库: {title[:30]}... ${price}")
                    except Exception as e:
                        print(f"❌ 数据库写入错误: {e}")
            # --- 核心循环结束 ---

            # 3. 发送邮件逻辑 (在 for item 循环外，但在 for task 循环内)
            if new_items_found:
                self.send_alert_email(new_items_found, task, task.target_email)
            else:
                print(f"📭 任务 [{task.keywords}] 本轮无新发现。")

    def send_alert_email(self, items_list, task, recipient):
        subject = f"🔥 发现 {len(items_list)} 个新上架的 {task.keywords}！"
        
        body = f"老板，你的监控任务 [{task.keywords}] 有新货了：\n"
        body += "="*45 + "\n\n"
        for i in items_list:
            body += f"💰 价格: ${i['price']}\n"
            body += f"📱 标题: {i['title']}\n"
            body += f"🔗 链接: {i['link']}\n"
            body += "-"*45 + "\n"
        
        try:
            send_mail(
                subject,
                body,
                None, # 使用 settings.py 里的 EMAIL_HOST_USER
                [recipient], # ✨ 这里改为动态变量 recipient
                fail_silently=False,
            )
            print(f"📢 成功发送邮件至: {recipient}") # 打印出具体发给谁了，方便调试
        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")