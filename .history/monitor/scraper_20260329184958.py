import undetected_chromedriver as uc
import random
import time
import re
from selenium.webdriver.common.by import By

def scrape_ebay(keywords, max_price):
    items = []
    # 每次调用都新建 options，防止 "reuse" 报错
    options = uc.ChromeOptions()
    options.add_argument('--lang=en-AU')
    
    driver = None
    try:
        # 1. 强制对齐你的 Chrome v146，这是昨天成功的关键
        driver = uc.Chrome(options=options, version_main=146)
        
        # 2. 昨天好用的 URL 模板
        url = f"https://www.ebay.com.au/sch/i.html?_nkw={keywords.replace(' ', '+')}&_udhi={max_price}&_ipg=60"
        
        driver.get(url)
        
        # 3. 给 UQ 网络留出充足的加载时间 (昨天可能网速快，今天稍微多等会)
        time.sleep(random.uniform(12, 15)) 
        
        # 4. 回到昨天最简单的选择器逻辑
        # 如果昨天是用 .s-item，我们就用 .s-item
        nodes = driver.find_elements(By.CSS_SELECTOR, ".s-item__wrapper")
        if not nodes:
            nodes = driver.find_elements(By.CSS_SELECTOR, ".s-item")

        print(f"DEBUG: 抓回了 {len(nodes)} 个原始数据")

        for node in nodes:
            try:
                title = node.find_element(By.CSS_SELECTOR, ".s-item__title").text
                price_str = node.find_element(By.CSS_SELECTOR, ".s-item__price").text
                link = node.find_element(By.CSS_SELECTOR, ".s-item__link").get_attribute("href")
                
                # 清洗价格
                price_num = float(re.findall(r"[\d.]+", price_str.replace(",", ""))[0])
                
                if "iphone" in title.lower():
                    items.append({'title': title, 'price': price_num, 'link': link})
            except:
                continue

    except Exception as e:
        print(f"❌ 运行出错: {e}")
    finally:
        if driver:
            driver.quit()

    return items