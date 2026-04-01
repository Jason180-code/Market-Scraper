from django.db import models
from django.contrib.auth.models import User

class WatchTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    keywords = models.CharField(max_length=255)  # 例如: "Herman Miller"
    max_price = models.DecimalField(max_digits=10, decimal_places=2)
    target_email = models.EmailField(default="zzj20050510@hotmail.com") # 默认邮箱，用户可修改
    platform = models.CharField(max_length=50, default="eBay") # 建议从易爬的平台开始
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    min_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, 
        verbose_name="最低限价 (用于过滤配件)"
    )
    must_contain = models.CharField(
        max_length=255, blank=True, 
        help_text="选填，多个词用逗号隔开。例如：GB,TB,Unlocked",
        verbose_name="必须包含的特征词"
    )

class ScrapedItem(models.Model):
    task = models.ForeignKey(WatchTask, on_delete=models.CASCADE)
    title = models.CharField(max_length=500)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    url = models.URLField(unique=True) # 唯一链接防止重复通知
    found_at = models.DateTimeField(auto_now_add=True)