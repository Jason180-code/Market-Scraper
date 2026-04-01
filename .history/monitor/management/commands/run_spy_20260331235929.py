import threading
import time
from queue import Queue
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone
from datetime import timedelta
from monitor.models import WatchTask, ScrapedItem
from monitor.scraper import scrape_ebay
from monitor.scraper import scrape_facebook

class Command(BaseCommand):
    help = '启动自动化监控哨兵'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- 市场监控哨兵已启动 ---'))

        while True:
            close_old_connections()  # 💡 关键：确保每次循环都从数据库获取最新状态
            # 1. 获取所有激活的任务
            tasks = WatchTask.objects.filter(is_active=True)
            
            if not tasks.exists():
                self.stdout.write(self.style.WARNING('⚠️ 没有激活的任务，等待中...'))
                time.sleep(60)
                continue

            for task in tasks:
                # 检查是否满足运行时间间隔（VIP 5分钟，普通1小时）
                if not self.should_run(task):
                    continue

                self.stdout.write(self.style.MIGRATE_LABEL(f'🔍 正在多平台搜寻: {task.keywords}'))
                
                # 2. 并发抓取多平台
                all_found = self.collect_all_platforms(task)

                # 3. 数据库去重与存储
                newly_discovered = self.process_and_save(task, all_found)

                # 4. 如果发现新商品，发送汇总提醒
                if newly_discovered:
                    self.send_combined_summary(task, newly_discovered)
                
                # 更新任务的最后运行时间
                task.last_run = timezone.now()
                task.save(update_fields=['last_run'])
                
                # 任务间稍作停顿
                time.sleep(5)
                
            # 每一轮任务扫完后休息 30 秒
            time.sleep(30)

    def should_run(self, task):
        """判断任务是否到了执行时间"""
        VIP_INTERVAL = 300      # 5 分钟
        NORMAL_INTERVAL = 3600  # 1 小时
        interval = VIP_INTERVAL if getattr(task, 'is_vip', False) else NORMAL_INTERVAL
        
        if task.last_run and (timezone.now() < task.last_run + timedelta(seconds=interval)):
            return False
        return True

    def collect_all_platforms(self, task):
        """核心重构：利用多线程同时抓取多个平台"""
        results_queue = Queue()
        # 定义需要并发执行的爬虫列表
        scrapers = [
            ('eBay', scrape_ebay),
            ('Facebook', scrape_facebook),
        ]
        
        threads = []
        
        # 逻辑判断：如果选的是 All，则加载 registry 里所有的
        # 如果选的是特定的，则只加载那一个
        selected_platform = task.platform # 这里拿到的就是 'All', 'eBay' 或 'Facebook'
        
        for name, func in scrapers:
            if selected_platform == 'All' or selected_platform == name:
                t = threading.Thread(
                    target=self.thread_worker, 
                    args=(name, func, task, results_queue)
                )
                threads.append(t)
                t.start()
        
        for t in threads:
            t.join()
            
        combined_results = []
        while not results_queue.empty():
            combined_results.extend(results_queue.get())
        return combined_results
    
    def thread_worker(self, name, scraper_func, task, queue):
        """线程工作函数，执行爬虫并将结果打上平台标签"""
        try:
            # 执行爬虫，传入 keywords, max_price, min_price
            found = scraper_func(task.keywords, float(task.max_price), float(task.min_price))
            # 给每个找到的项目添加平台来源标记
            for item in found:
                item['platform'] = name
            queue.put(found)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ {name} 抓取线程异常: {e}"))
            queue.put([])

    def process_and_save(self, task, items):
        """去重逻辑：检查 URL 是否已存在，并保存新商品"""
        new_items = []
        self.stdout.write(self.style.HTTP_INFO(f"📊 正在处理从平台获取的 {len(items)} 个商品...")) 
        for item in items:
            # 1. 基础去重：检查 URL 是否已在数据库中
            if not ScrapedItem.objects.filter(url=item['link']).exists():
                
                # 2. 标题关键词二次过滤（排除配件或损坏件）
                title_lower = item['title'].lower()
                if any(word in title_lower for word in ["broken", "parts", "faulty", "repair"]):
                    continue

                # 3. 存入数据库（确保模型中有 platform 字段）
                obj = ScrapedItem.objects.create(
                    task=task,
                    title=item['title'],
                    price=item['price'],
                    url=item['link'],
                    platform=item.get('platform', 'eBay')
                )
                new_items.append(obj)
                new_items.append(item)
        return new_items

    def send_combined_summary(self, task, items):
    """发送多平台汇总邮件"""
    # 1. 内存去重：防止并发导致的同一商品多次出现在同一封邮件
    seen_urls = set()
    unique_items = []
    for it in items:
        # 兼容对象和字典提取 URL
        u = it.url if hasattr(it, 'url') else it.get('link', it.get('url'))
        if u and u not in seen_urls and u != '#':
            seen_urls.add(u)
            unique_items.append(it)
    items = unique_items

    if not items:
        return

    # 2. 排序逻辑
    items.sort(key=lambda x: float(x.price) if hasattr(x, 'price') else float(x.get('price', 0)))

    is_vip = getattr(task, 'is_vip', False)
    
    # 差异化标题和页眉
    subject = f"🔥 [VIP 极速全网汇总] 发现 {len(items)} 件新低价！" if is_vip else f"📩 [多平台捡漏简报] 发现 {len(items)} 件新商品"
    header_text = "✨ 尊敬的 VIP 用户，已为您同步监控 eBay 与 Facebook Marketplace：" if is_vip else "💡 哨兵已完成多平台扫描，最新汇总如下："

    content_lines = [
        f"你好 {task.user.username}，",
        f"\n{header_text}",
        "\n" + "="*40
    ]
    
    for i, item in enumerate(items, 1):
        is_obj = hasattr(item, 'price') 
        
        # 确保 price 是数字，避免拼接失败
        price = item.price if is_obj else item.get('price', '0')
        title = item.title if is_obj else item.get('title', 'Unknown')
        # 核心修复点：优先尝试 link 键名
        url = item.url if is_obj else item.get('link', item.get('url', '#'))
        platform = item.platform if is_obj else item.get('platform', 'eBay')
        
        platform_label = f"[{platform}]"
        icon = "🔥 " if is_vip and i <= 3 else f"{i}. "
        
        content_lines.append(f"{icon}{platform_label} 【${price}】{title}")
        content_lines.append(f"   👉 链接: {url}\n")
        
        try:
            send_mail(
                subject,
                "\n".join(content_lines),
                settings.EMAIL_HOST_USER,
                [task.user.email],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f"  ✅ 汇总邮件已发出至: {task.user.email}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ❌ 邮件发送失败: {e}"))