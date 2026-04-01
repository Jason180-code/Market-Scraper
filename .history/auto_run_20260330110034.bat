@echo off
cd /d E:\MarketPachong
:: 激活虚拟环境并运行 Django 命令
call venv\Scripts\activate
python manage.py run_spy
echo 扫描完成，600秒后再次扫描...
timeout /t 600
goto loop