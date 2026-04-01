@echo off
cd /d E:\MarketPachong
:: 激活虚拟环境并运行 Django 命令
call venv\Scripts\activate
python manage.py run_spy
