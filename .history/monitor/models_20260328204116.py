from django.db import models
from django.contrib.auth.models import User

class WatchTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    keywords = models.CharField(max_length=255)  # 例如: "Herman Miller"
    max_price = models.DecimalField(max_digits=10, decimal_places=2)
    platform = models.CharField(max_length=50, default="eBay") # 建议从易爬的平台开始
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ScrapedItem(models.Model):
    task = models.ForeignKey(WatchTask, on_delete=models.CASCADE)
    title = models.CharField(max_length=500)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    url = models.URLField(unique=True) # 唯一链接防止重复通知
    found_at = models.DateTimeField(auto_now_add=True)