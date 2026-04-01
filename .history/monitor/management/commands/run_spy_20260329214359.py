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

        for task in tasks:
            self.stdout.write(f'🔍 正在为用户 [{task.user.username}] 扫描: {task.keywords}')
    
    # 执行爬取
    found_items = scrape_ebay(task.keywords, task.max_price)
    
    for item in found_items:
        # 1. 唯一性检查（防止重复发送同一条链接）
        if not ScrapedItem.objects.filter(url=item['link']).exists():
            
            # 2. 需求匹配（示例：标题必须包含任务指定的关键词）
            # 你可以增加更复杂的判断，比如 task.min_storage (256GB) 等
            
            # 保存到数据库
            new_item = ScrapedItem.objects.create(
                task=task,
                title=item['title'],
                price=item['price'],
                url=item['link']
            )

            # 3. 获取该任务对应的邮箱
            target_email = task.user.email
            
            if target_email:
                subject = f"🔔 [捡漏提醒] {task.keywords} - ${item['price']}"
                # 针对不同人定制内容
                message = (
                    f"嗨 {task.user.username}，\n\n"
                    f"根据你的监控需求「{task.keywords}」，我们发现了新货：\n"
                    f"---------------------------------\n"
                    f"物品: {item['title']}\n"
                    f"价格: ${item['price']}\n"
                    f"链接: {item['link']}\n"
                    f"---------------------------------\n"
                    f"祝捡漏成功！"
                )

                try:
                    send_mail(
                        subject,
                        message,
                        settings.EMAIL_HOST_USER, # 发件人（你在 settings 里的配置）
                        [target_email],           # 收件人（动态获取）
                        fail_silently=False,
                    )
                    self.stdout.write(self.style.SUCCESS(f"📧 已推送到: {target_email}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ 邮件发送给 {target_email} 失败: {e}"))