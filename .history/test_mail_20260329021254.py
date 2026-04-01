import os
import django
from django.core.mail import send_mail

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MarketPachong.settings') # 确保这里的名字和你的文件夹一致
django.setup()

def send_test():
    try:
        print("正在尝试发送邮件...")
        send_mail(
            'MarketSpy 测试邮件',
            '看到这条信息说明你的 Outlook 配置成功了！准备好抢 iPhone 吧！',
            '你的邮箱@outlook.com',  # 发件人
            ['你的邮箱@outlook.com'],  # 收件人（发给自己）
            fail_silently=False,
        )
        print("✅ 发送成功！请检查你的收件箱（包括垃圾邮件箱）。")
    except Exception as e:
        print(f"❌ 发送失败，报错信息: {e}")

if __name__ == "__main__":
    send_test()