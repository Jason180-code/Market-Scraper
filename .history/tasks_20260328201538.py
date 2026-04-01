import requests
from bs4 import BeautifulSoup
from celery import shared_task
from .models import WatchTask, ScrapedItem

@shared_task
def check_marketplaces():
    # 1. 获取所有激活的监控任务
    active_tasks = WatchTask.objects.filter(is_active=True)
    
    for task in active_tasks:
        # 2. 执行爬虫逻辑 (以某二手平台搜索页为例)
        search_url = f"https://example-marketplace.com/search?q={task.keywords}"
        response = requests.get(search_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 3. 解析页面上的商品条目
        items = soup.find_all('div', class_='item-card')
        for item in items:
            title = item.find('h3').text
            price = float(item.find('span', class_='price').text.replace('$', ''))
            link = item.find('a')['href']
            
            # 4. 核心过滤逻辑：价格符合 & 之前没抓过
            if price <= task.max_price:
                if not ScrapedItem.objects.filter(url=link).exists():
                    # 保存到数据库
                    ScrapedItem.objects.create(task=task, title=title, price=price, url=link)
                    # 5. 触发通知函数
                    send_notification(task.user, title, price, link)

def send_notification(user, title, price, link):
    # 这里可以集成邮件 API (如 SendGrid) 或 微信推送
    print(f"通知用户 {user.username}: 发现好货！{title} 仅售 ${price}, 链接: {link}")