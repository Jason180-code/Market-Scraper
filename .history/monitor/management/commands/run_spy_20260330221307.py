import time
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from monitor.models import WatchTask, ScrapedItem
from monitor.scraper import scrape_ebay

class Command(BaseCommand):
    help = '启动自动化监控哨兵'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- 市场监控哨兵已启动 ---'))
        
        # 设定不同等级的检查频率（秒）
        VIP_INTERVAL = 300      # VIP 每 5 分钟检查一次
        NORMAL_INTERVAL = 3600  # 普通用户每 1 小时检查一次

        while True:
            # 1. 获取所有激活的任务
            tasks = WatchTask.objects.filter(is_active=True)
            
            if not tasks.exists():
                self.stdout.write(self.style.WARNING('⚠️ 没有激活的任务，等待中...'))
                time.sleep(60)
                continue

            for task in tasks:
                now = timezone.now()
                
                # --- VIP 逻辑核心：判断是否到了该干活的时间 ---
                # 获取该任务上次运行后的冷却时间
                interval = VIP_INTERVAL if getattr(task, 'is_vip', False) else NORMAL_INTERVAL
                
                # 检查是否满足运行条件（如果是第一次运行，或者距离上次运行已超过设定间隔）
                # 注意：你需要在模型里有 last_run 字段，如果没有，逻辑会默认每次都跑
                last_run = getattr(task, 'last_run', None)
                if last_run and (now < last_run + timedelta(seconds=interval)):
                    continue 

                self.stdout.write(self.style.MIGRATE_LABEL(
                    f'🔍 [{"VIP" if getattr(task, "is_vip", False) else "普通"}] 正在检查: {task.user.username} 的关键词 [{task.keywords}]'
                ))

                # 2. 执行爬虫
                found_items = scrape_ebay(task.keywords, task.max_price)
                
                newly_discovered = []
                for item in found_items:
                    if not ScrapedItem.objects.filter(url=item['link']).exists():
                        # 简单的过滤逻辑
                        if any(word in item['title'].lower() for word in ["broken", "parts", "faulty"]):
                            continue

                        ScrapedItem.objects.create(
                            task=task,
                            title=item['title'],
                            price=item['price'],
                            url=item['link']
                        )
                        newly_discovered.append(item)

                # 3. 发送提醒
                if newly_discovered and task.user.email:
                    self.send_summary_email(task, newly_discovered)
                
                # 更新任务的最后运行时间
                if hasattr(task, 'last_run'):
                    task.last_run = now
                    task.save(update_fields=['last_run'])
                
                # 任务间微调，防止 eBay 识别异常
                time.sleep(5)

            # 哨兵呼吸时间：每分钟扫一次数据库看有没有新到期的任务
            time.sleep(60)

    def send_summary_email(self, task, items):
        # 所有人统一按价格升序排序（建立好感度）
        items.sort(key=lambda x: x['price']) 
        
        is_vip = getattr(task, 'is_vip', False)
        
        # --- 差异化标题 ---
        if is_vip:
            subject = f"🔥 [VIP 极速优先] 发现 {len(items)} 件新低价！"
            header_text = "✨ 尊敬的 VIP 用户，为您锁定全网最低价："
        else:
            subject = f"📩 [每日捡漏简报] 发现 {len(items)} 件新商品"
            header_text = "💡 今日部分低价商品汇总（普通频率）："

        content_lines = [
            f"你好 {task.user.username}，",
            f"\n{header_text}",
            "\n" + "="*30
        ]
        
        for i, item in enumerate(items, 1):
            # --- 差异化展示：VIP 看到火苗，普通用户看到序号 ---
            icon = "🔥 " if is_vip and i <= 3 else f"{i}. "
            content_lines.append(f"{icon}【${item['price']}】{item['title']}")
            content_lines.append(f"   👉 查看详情: {item['link']}\n")
        
        # --- 差异化结尾：给普通用户留个“钩子” ---
        content_lines.append("="*30)
        if not is_vip:
            content_lines.append("\n⏰ 提示：当前为每小时刷新。想开启 5 分钟极速监控？私聊大神开通 VIP 吧！")
        
        content_lines.append("\n祝你在布里斯班捡漏成功！")
        
        # 发送逻辑保持不变...
        
        try:
            send_mail(
                subject,
                "\n".join(content_lines),
                settings.EMAIL_HOST_USER,
                [task.user.email],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f"  ✅ 邮件已发出至: {task.user.email}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ❌ 邮件发送失败: {e}"))