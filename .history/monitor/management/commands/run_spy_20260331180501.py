import time
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone
from datetime import timedelta
from monitor.models import WatchTask, ScrapedItem
from monitor.scraper import scrape_ebay

class Command(BaseCommand):
    help = '启动自动化监控哨兵'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 哨兵 2.0 并发架构已启动...'))
        
        while True:
            close_old_connections()
            tasks = WatchTask.objects.filter(is_active=True).select_related('user')
            
            for task in tasks:
                if not self.should_run(task):
                    continue

                self.stdout.write(self.style.MIGRATE_LABEL(f'🔍 正在多平台搜寻: {task.keywords}'))
                
                # 并发收集
                results_q = Queue()
                scrapers = [scrape_ebay, scrape_facebook]
                threads = [threading.Thread(target=lambda f: results_q.put(f(task.keywords, task.max_price, task.min_price)), args=(func,)) for func in scrapers]
                
                for t in threads: t.start()
                for t in threads: t.join()

                all_found = []
                while not results_q.empty(): all_found.extend(results_q.get())

                # 去重与存储
                new_items = []
                for item in all_found:
                    if not ScrapedItem.objects.filter(url=item['link']).exists():
                        ScrapedItem.objects.create(task=task, title=item['title'], price=item['price'], url=item['link'], platform=item['platform'])
                        new_items.append(item)

                if new_items:
                    self.send_combined_email(task, new_items)
                
                task.last_run = timezone.now()
                task.save(update_fields=['last_run'])
            time.sleep(30)

    def should_run(self, task):
        VIP_INTERVAL = 300
        NORMAL_INTERVAL = 3600
        interval = VIP_INTERVAL if task.is_vip else NORMAL_INTERVAL
        if task.last_run and (timezone.now() < task.last_run + timedelta(seconds=interval)):
            return False
        return True

    def collect_all_platforms(self, task):
        results_queue = Queue()
        # 定义要跑的任务列表
        scrapers = [
            ('eBay', scrape_ebay),
            ('Gumtree', scrape_gumtree),
        ]
        
        threads = []
        for name, func in scrapers:
            t = threading.Thread(target=self.thread_worker, args=(func, task, results_queue))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
            
        combined = []
        while not results_queue.empty():
            combined.extend(results_queue.get())
        return combined

    def thread_worker(self, scraper_func, task, queue):
        try:
            # 统一传入数据库中定义的 min_price
            items = scraper_func(task.keywords, float(task.max_price), float(task.min_price))
            queue.put(items)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"线程运行异常: {e}"))
            queue.put([])

    def process_and_save(self, task, items):
        new_items = []
        for item in items:
            # 基础去重：URL + 标题
            if not ScrapedItem.objects.filter(url=item['link']).exists():
                # 再次过滤常见的垃圾词（作为第二道防线）
                if any(word in item['title'].lower() for word in ["broken", "parts", "faulty"]):
                    continue

                ScrapedItem.objects.create(
                    task=task,
                    title=item['title'],
                    price=item['price'],
                    url=item['link']
                )
                new_items.append(item)
        return new_items

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