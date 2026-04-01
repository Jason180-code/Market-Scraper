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
            print(f"🔍 正在执行任务: [{task.keywords}] (最高限价: ${task.max_price})")
            
            # 2. 调用爬虫获取原始数据
            items = scrape_ebay(task.keywords, float(task.max_price))
            
            new_items_found = []
            kw_lower = task.keywords.lower()
            
            # 干扰词列表：排除非目标品牌的竞争对手和配件
            noise_words = ['samsung', 'google', 'pixel', 'nokia', 'motorola', 'case', 'box only', 'parts', 'damaged']

            for item in items:
                title = item['title']
                title_lower = title.lower()
                
                # --- 🛑 过滤器逻辑 (修复点) ---
                is_invalid = False
                
                # A. 关键词包含校验：标题里必须有监控词（比如 iPhone 13）
                if kw_lower not in title_lower:
                    is_invalid = True
                
                # B. 干扰词深度校验：如果标题有噪音词，且噪音词不是监控词本身
                else:
                    for noise in noise_words:
                        if noise in title_lower and noise not in kw_lower:
                            is_invalid = True
                            break
                
                # 如果校验不通过，跳过该商品
                if is_invalid:
                    # print(f"⏩ 过滤无效项: {title[:30]}...") # 调试时可开启
                    continue
                
                # --- ✅ 数据库查重与保存 ---
                if not ScrapedItem.objects.filter(url=item['link']).exists():
                    try:
                        ScrapedItem.objects.create(
                            task=task,
                            title=title,
                            price=item['price'],
                            url=item['link']
                        )
                        new_items_found.append(item)
                        print(f"✨ 发现新货: {title[:40]}... ${item['price']}")
                    except Exception as e:
                        print(f"❌ 存入数据库失败: {e}")

            # 3. 如果该任务有新发现，发送邮件
            if new_items_found:
                self.send_alert_email(new_items_found, task)
            else:
                print(f"📭 任务 [{task.keywords}] 本轮无新发现。")

    def send_alert_email(self, items_list, task):
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
                ['zzj20050510@hotmi'], # 填入你的 UQ 邮箱
                fail_silently=False,
            )
            print(f"📢 成功发送邮件至个人邮箱！")
        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")