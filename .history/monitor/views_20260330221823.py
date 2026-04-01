# views.py
from django.shortcuts import render
from .models import MonitorTask, UserProfile

def add_monitor_task(request):
    user_profile = request.user.userprofile
    limit = user_profile.get_task_limit()
    
    # 统计当前用户已经激活的任务数
    current_tasks_count = MonitorTask.objects.filter(user=request.user, is_active=True).count()
    
    if current_tasks_count >= limit:
        return JsonResponse({
            "status": "error", 
            "message": f"达到上限！普通用户仅支持 {limit} 个任务，升级 VIP 可解锁至 5 个。"
        })

# Create your views here.
