from django.db import models
from django.contrib.auth.models import User

class WatchTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    keywords = models.CharField(max_length=255)
    
    # 价格区间
    min_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # 过滤与匹配逻辑
    must_contain = models.CharField(max_length=255, blank=True)
    
    # 任务控制
    is_active = models.BooleanField(default=True)
    is_vip = models.BooleanField(default=False)
    check_interval = models.IntegerField(default=60) # 分钟
    last_run = models.DateTimeField(null=True, blank=True)
    
    # 通知设置
    platform = models.CharField(max_length=50, default="Al")
    target_email = models.EmailField(default="zzj20050510@hotmail.com")
    wechat_push_key = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.keywords}"

class ScrapedItem(models.Model):
    task = models.ForeignKey(WatchTask, on_delete=models.CASCADE)
    title = models.CharField(max_length=500)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    url = models.URLField(unique=True) # 唯一链接防止重复通知
    found_at = models.DateTimeField(auto_now_add=True)