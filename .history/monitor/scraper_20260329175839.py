import time
import random
import re
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_ebay(keywords, max_price):
    edge_options = Options()
    edge_options.add_argument("--disable-gpu")
    # 进一步伪装：禁用闪烁的自动化提示
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    edge_options.add_experimental_option('useAutomationExtension', False)
    edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0")

    service = Service(executable_path=r"E:\MarketPachong\msedgedriver.exe")
    driver = webdriver.Edge(service=service, options=edge_options)

    # 再次抹除指纹
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    url = f"https://www.ebay.com.au/sch/i.html?_nkw={keywords}&_udhi={max_price}&_sop=12"
    items = []

    try:
        # ✨ 关键优化 1：只查找真正的商品列表项
        # eBay 的标准商品卡片类名通常是 .s-item__wrapper 或 .s-item
        # 我们使用这个选择器可以过滤掉侧边栏、页眉和广告
        items_elements = driver.find_elements(By.CSS_SELECTOR, ".s-item__wrapper")
        
        # ✨ 添加这一行调试！
    print(f"DEBUG: 页面上一共找到了 {len(items_elements)} 个商品卡片")
    
    # 如果 len 是 0，说明 CSS 选择器失效了
    if len(items_elements) == 0:
        # 尝试备用选择器
        items_elements = driver.find_elements(By.CSS_SELECTOR, ".s-item")
        print(f"DEBUG: 尝试备用选择器，找到了 {len(items_elements)} 个")
        items = []
        for el in items_elements:
            try:
                # ✨ 关键优化 2：在卡片内部精准查找标题、价格和链接
                # 使用相对路径 ( .// ) 确保只在该卡片内搜索
                title_el = el.find_element(By.CSS_SELECTOR, ".s-item__title")
                price_el = el.find_element(By.CSS_SELECTOR, ".s-item__price")
                link_el = el.find_element(By.CSS_SELECTOR, ".s-item__link")
                
                title = title_el.text.strip()
                # 过滤掉 eBay 自动生成的 "New Listing" 等干扰字眼
                title = title.replace("New Listing", "").strip()
                
                price_text = price_el.text.replace("AU ", "").replace("$", "").replace(",", "").strip()
                # 处理价格区间（例如 "150.00 to 200.00"），只取最低价
                if " to " in price_text:
                    price_text = price_text.split(" to ")[0]
                
                price = float(price_text)
                link = link_el.get_attribute("href")

                # 只有标题不为空且价格在合理范围内才添加
                if title and price > 0:
                    items.append({
                        'title': title,
                        'price': price,
                        'link': link
                    })
            except Exception:
                # 某些卡片可能是空的广告位，直接跳过即可
                continue

    finally:
        driver.quit()
    
    return items