from django.core.management.base import BaseCommand
from monitor.models import WatchTask, ScrapedItem
from monitor.scraper import scrape_ebay  # 导入你写的爬虫逻辑

class Command(BaseCommand):
    help = '手动触发爬虫扫描任务'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- 市场扫描开始 ---'))
        
        # 1. 获取所有激活的监控任务
        tasks = WatchTask.objects.filter(is_active=True)
        
        if not tasks.exists():
            self.stdout.write(self.style.WARNING('当前没有激活的任务。请先在数据库中添加一个 WatchTask。'))
            # 为了测试，我们自动创建一个
            task = WatchTask.objects.create(keywords="iPhone 13", max_price=600)
            self.stdout.write(f'已自动创建测试任务: {task.keywords}')
            tasks = [task]

        for task in tasks:
            self.stdout.write(f'正在扫描: {task.keywords} (最高限价: ${task.max_price})')
            
            # 2. 调用 scraper.py 里的函数
            # 注意：确保你的 scraper.py 里的函数名是 scrape_ebay
            found_items = scrape_ebay(task.keywords, task.max_price)
            
            new_count = 0
            for item in found_items:
                # 3. 查重逻辑：URL 是唯一的，如果数据库里没有这个链接，说明是新发布的
                if not ScrapedItem.objects.filter(url=item['link']).exists():
                    ScrapedItem.objects.create(
                        task=task,
                        title=item['title'],
                        price=item['price'],
                        url=item['link']
                    )
                    self.stdout.write(self.style.NOTICE(f"  [新发现!] {item['title']} - ${item['price']}"))
                    new_count += 1
            
            self.stdout.write(self.style.SUCCESS(f'任务 {task.keywords} 完成，新增 {new_count} 个商品。'))

        self.stdout.write(self.style.SUCCESS('--- 所有扫描任务已结束 ---'))