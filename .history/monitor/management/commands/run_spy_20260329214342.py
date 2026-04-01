from django.core.management.base import BaseCommand
from django.contrib.auth.models import User  # 导入用户模型
from monitor.models import WatchTask, ScrapedItem
from monitor.scraper import scrape_ebay

class Command(BaseCommand):
    help = '手动触发爬虫扫描任务'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- 市场扫描开始 ---'))
        
        # 1. 尝试获取第一个用户（就是你刚才建的那个）
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR('错误：请先运行 python manage.py createsuperuser 创建用户'))
            return

        # 2. 获取所有激活的任务
        tasks = WatchTask.objects.filter(is_active=True)
        
        if not tasks.exists():
            self.stdout.write(self.style.WARNING('没有激活任务，正在创建测试任务...'))
            # 创建任务时，把 user 传进去
            task = WatchTask.objects.create(
                user=user, 
                keywords="iPhone 13", 
                max_price=600
            )
            tasks = [task]

        # 后面的逻辑保持不变...
        for task in tasks:
            self.stdout.write(f'正在扫描: {task.keywords} (限价: ${task.max_price})')
            found_items = scrape_ebay(task.keywords, task.max_price)
            
            new_count = 0
            for item in found_items:
                if not ScrapedItem.objects.filter(url=item['link']).exists():
                    ScrapedItem.objects.create(
                        task=task,
                        title=item['title'],
                        price=item['price'],
                        url=item['link']
                    )
                    self.stdout.write(self.style.NOTICE(f"  [新发现!] {item['title']} - ${item['price']}"))
                    new_count += 1
            
            self.stdout.write(self.style.SUCCESS(f'任务 {task.keywords} 完成，新增 {new_count} 个。'))