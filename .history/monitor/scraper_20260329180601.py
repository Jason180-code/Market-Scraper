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
    # 1. 变量初始化（放在最外面，防止 UnboundLocalError）
    items = [] 
    
    edge_options = Options()
    # 调试建议：暂时注释掉 headless，亲眼看看浏览器在干嘛
    # edge_options.add_argument("--headless") 
    edge_options.add_argument("--disable-blink-features=AutomationControlled")
    edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0")

    service = Service(executable_path=r"E:\MarketPachong\msedgedriver.exe")
    driver = webdriver.Edge(service=service, options=edge_options)

    try:
        # 2. 执行抓取
        url = f"https://www.ebay.com.au/sch/i.html?_nkw={keywords.replace(' ', '+')}&_udhi={max_price}"
        driver.get(url)
        
        print("DEBUG: 模拟真人行为中...")
        time.sleep(random.uniform(2, 4)) 

        # ⏳ 显式等待：改为寻找通用容器
        wait = WebDriverWait(driver, 15)
        print("DEBUG: 正在尝试定位商品标题...")
        
        # 这里的报错通常是因为页面没加载出 .s-item__title
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".s-item__title")))

        items_elements = driver.find_elements(By.CSS_SELECTOR, ".s-item__wrapper")
        print(f"DEBUG: 找到了 {len(items_elements)} 个商品块")

        for el in items_elements:
            try:
                title = el.find_element(By.CSS_SELECTOR, ".s-item__title").text.replace("New Listing", "").strip()
                if not title or "Shop on eBay" in title: continue

                price_text = el.find_element(By.CSS_SELECTOR, ".s-item__price").text
                # 使用更简单的正则提取数字
                price_match = re.search(r"[\d,.]+", price_text.replace(",", ""))
                price = float(price_match.group()) if price_match else 0
                
                link = el.find_element(By.CSS_SELECTOR, ".s-item__link").get_attribute("href")

                if title and price > 0:
                    items.append({'title': title, 'price': price, 'link': link})
            except:
                continue

    except Exception as e:
        print(f"❌ 抓取出错: {e}")
        driver.save_screenshot("error_debug.png") # 记录案发现场
    finally:
        driver.quit()

    return items # 此时即使报错，也能返回 []，不会再报 UnboundLocalError