import os
import datetime
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
        if not tasks.exists():
            print("📭 没有激活的监控任务，请在 Admin 后台添加。")
            return

        for task in tasks:
            print(f"🔍 执行任务: [{task.keywords}] | 限价: ${task.min_price} - ${task.max_price}")
            
            items = scrape_ebay(task.keywords, float(task.max_price))
            new_items_found = []
            kw_lower = task.keywords.lower()
            
            for item in items:
                title = item['title']
                title_lower = title.lower()
                price = float(item['price'])

                # --- 🛑 过滤器第一关：黑名单 ---
            is_invalid = False
            for noise in noise_words:
                if noise in title_lower:
                    is_invalid = True
                    break
            if is_invalid: continue

            # --- 🛑 过滤器第二关：价格区间 (Task 设置) ---
            if price < float(task.min_price):
                continue  # <--- 此时 $3.99 的商品在这里被拦截了，不会执行后面的代码
                
            if price > float(task.max_price):
                continue

            # --- 🛑 过滤器第三关：真机特征 ---
            if task.must_contain:
                required_words = [w.strip().lower() for w in task.must_contain.split(',')]
                if not any(word in title_lower for word in required_words):
                    continue

            # --- ✨ 只有走到这里的，才是真正的“好货” ---
            print(f"💎 成功通过过滤: {title[:40]}... ${price}")

                # --- ✅ 3. 查重与保存 ---
            if not ScrapedItem.objects.filter(url=item['link']).exists():
                    try:
                        ScrapedItem.objects.create(
                            task=task,
                            title=title,
                            price=price, # 存储清洗后的数字
                            url=item['link']
                        )
                        new_items_found.append(item)
                        print(f"✨ 发现好货: {title[:30]}... ${current_price}")
                    except Exception as e:
                        print(f"❌ 数据库写入错误: {e}")

            # 3. 如果该任务有新发现，发送邮件
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