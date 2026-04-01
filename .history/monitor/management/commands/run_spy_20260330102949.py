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
            self.stdout.write(self.style.WARNING('没有激活任务。'))
            return

        # --- 核心循环：开始对齐 ---
        for task in tasks:
            # 这里的代码属于 handle -> for task
            self.stdout.write(self.style.MIGRATE_LABEL(f'🔍 任务开始: 用户 [{task.user.username}] -> 关键词: {task.keywords}'))
            
            # 2. 调用爬虫 (传入当前任务的参数)
            found_items = scrape_ebay(task.keywords, task.max_price)
            
            new_count = 0
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
                        subject = f"🚀 [捡漏日报] 为你发现 {len(newly_discovered)} 件新商品！"
                    
                    # 6. 精准邮件投送
                    target_email = task.user.email
                    if target_email:
                        subject = f"🔔 [捡漏提醒] {task.keywords} - ${item['price']}"
                        # 构建汇总内容
                content_lines = [f"嗨 {task.user.username}，本次扫描为您发现以下符合需求的内容：\n"]
                for i, item in enumerate(newly_discovered, 1):
                    content_lines.append(f"{i}. 【${item['price']}】{item['title']}")
                    content_lines.append(f"   链接: {item['link']}\n")
                
                content_lines.append("祝ni捡漏成功！")
                full_message = "\n".join(content_lines)

                try:
                    send_mail(
                        subject,
                        full_message,
                        settings.EMAIL_HOST_USER,
                        [task.user.email],
                        fail_silently=False,
                    )
                    self.stdout.write(self.style.SUCCESS(f"  📧 汇总邮件已发送至: {task.user.email} ({len(newly_discovered)}个项目)"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  ❌ 邮件发送失败: {e}"))
            else:
                self.stdout.write(f"  ☕ 本轮无新发现，未触发邮件。")