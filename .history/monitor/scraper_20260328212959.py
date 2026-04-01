import re
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_ebay(keywords, max_price):
    # 1. 配置 Edge 选项
    edge_options = Options()
    # 稳定后可以取消下面这行的注释，开启无头模式（不弹窗）
    # edge_options.add_argument("--headless") 
    edge_options.add_argument("--disable-gpu")
    edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # 2. 初始化驱动 (指向你手动下载的路径)
    service = Service(executable_path=r"E:\MarketPachong\msedgedriver.exe")
    driver = webdriver.Edge(service=service, options=edge_options)

    url = f"https://www.ebay.com.au/sch/i.html?_nkw={keywords}&_udhi={max_price}&_sop=12"
    
    items = []
    try:
        print(f"DEBUG: 正在打开页面并等待渲染: {url}")
        driver.get(url)
        
        # 3. 显式等待：直到页面上出现了商品标题 (最多等 15 秒)
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "s-item__title"))
            )
        except:
            print("DEBUG: 等待超时，可能页面加载太慢或类名变了")

        # 4. 模拟向下滑动，触发懒加载内容
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(2)

        # 5. 开始解析
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 使用正则表达式模糊匹配所有可能的商品块
        results = soup.find_all('div', class_=re.compile(r's-item', re.I))
        print(f"DEBUG: 原始搜索到了 {len(results)} 个潜在块")

        for result in results:
            try:
                # 提取标题 (h3 或特定类名)
                title_node = result.find(['div', 'h3'], class_='s-item__title') or result.find('h3')
                if not title_node or "Shop on eBay" in title_node.text:
                    continue
                
                title = title_node.get_text(strip=True).replace("New Listing", "")

                # 提取价格
                price_node = result.select_one('.s-item__price')
                if not price_node:
                    continue
                
                price_text = price_node.get_text(strip=True)
                # 清洗价格数字 (例如: AU $1,200.00 -> 1200.0)
                price_digits = re.sub(r'[^\d.]', '', price_text.split()[-1])
                if not price_digits