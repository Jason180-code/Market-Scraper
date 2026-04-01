import time
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from monitor.models import WatchTask, ScrapedItem
from monitor.scraper import scrape_ebay

class Command(BaseCommand):
    help = '手动触发爬虫扫描任务'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- 市场扫描开始 ---'))
        
        # 1. 获取所有激活的任务
        tasks = WatchTask.objects.filter(is_active=True)
        
        if not tasks.exists():
            self.stdout.write(self.style.WARNING('⚠️ 没有激活的任务，请在 Admin 后台添加。'))
            return

        # --- 核心循环：开始对齐 ---
        for task in tasks:
           # 动态获取当前任务的用户
            current_user = task.user
            
            self.stdout.write(self.style.MIGRATE_LABEL(
                f'🔍 任务开始: 用户 [{current_user.username}] -> 邮箱: {current_user.email}'
            ))

            # 2. 调用爬虫 (传入当前任务的参数)
            found_items = scrape_ebay(task.keywords, task.max_price)
            
            newly_discovered = []
            
            for item in found_items:
                # 这里的代码属于 handle -> for task -> for item
                
                # 3. 唯一性检查
                if not ScrapedItem.objects.filter(url=item['link']).exists():
                    
                    # 4. 这里的需求匹配可以根据任务字段扩展 (比如过滤 Broken)
                    if "broken" in item['title'].lower() or "parts" in item['title'].lower():
                        continue

                    # 5. 保存数据
                    ScrapedItem.objects.create(
                        task=task,
                        title=item['title'],
                        price=item['price'],
                        url=item['link']
                    )

                    newly_discovered.append(item)
                    
            if newly_discovered and task.user.email:
                dest_email = current_user.email
                
                subject = f"ebay发现 {len(newly_discovered)} 件新商品！"
                
                content_lines = [f"嗨 {task.user.username}，本次扫描为您发现以下符合需求的内容：\n"]
                for i, idx_item in enumerate(newly_discovered, 1):
                    content_lines.append(f"{i}. 【${idx_item['price']}】{idx_item['title']}")
                    content_lines.append(f"   链接: {idx_item['link']}\n")
                
                content_lines.append("祝你捡漏成功！")
                full_message = "\n".join(content_lines)

                try:
                    send_mail(
                        subject,
                        full_message,
                        settings.EMAIL_HOST_USER,
                        [dest_email], # 使用动态获取的 dest_email
                        fail_silently=False,
                    )
                    self.stdout.write(self.style.SUCCESS(f"  📧 汇总邮件已发送至: {task.user.email} ({len(newly_discovered)}个项目)"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  ❌ 邮件发送失败: {e}"))
            else:
                self.stdout.write(f"  ☕ 本轮无新发现（或无有效邮箱），未触发邮件。")
            
            # 在处理下一个任务前稍微歇会儿，防止 eBay 封 IP
            time.sleep(2)

        self.stdout.write(self.style.SUCCESS('\n--- 所有扫描任务已完成 ---'))