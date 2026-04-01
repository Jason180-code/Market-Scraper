import os
import django
from django.core.mail import send_mail

# 1. 告诉脚本去哪里找你的 Django 配置
# 注意：如果你的项目文件夹名字不是 MarketPachong，请修改下面这行
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MarketPachong.settings')

# 2. 启动 Django 环境
django.setup()

def send_test():
    try:
        print("🚀 正在尝试通过 Gmail 发送测试邮件...")
        
        # 3. 执行发送
        send_mail(
            subject='MarketSpy: 邮件系统测试',
            message='如果你在学校 Outlook 邮箱里看到这条信息，说明监控系统已就绪！',
            from_email=None,  # 留空会自动使用 settings.py 里的 EMAIL_HOST_USER
            recipient_list=['s498344@student.uq.edu.au'], # 这里填你的 UQ 学校邮箱
            fail_silently=False,
        )
        
        print("✅ 发送成功！快去检查你的 UQ 学校邮箱（包括 Junk 文件夹）。")
        
    except Exception as e:
        print(f"❌ 发送失败！错误原因:\n{e}")

if __name__ == "__main__":
    send_test()