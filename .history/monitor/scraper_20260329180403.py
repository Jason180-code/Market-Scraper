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
    # --- 1. 核心伪装：移除自动化标记 ---
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    edge_options.add_experimental_option('useAutomationExtension', False)
    
    # --- 2. 避免被检测为 Headless (即使你现在开着窗口) ---
    edge_options.add_argument("--disable-blink-features=AutomationControlled")
    edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0")

    service = Service(executable_path=r"E:\MarketPachong\msedgedriver.exe")
    driver = webdriver.Edge(service=service, options=edge_options)

    # --- 3. 注入更强大的指纹抹除脚本 ---
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    # 1. 构造 URL
    url = f"https://www.ebay.com.au/sch/i.html?_nkw={keywords.replace(' ', '+')}&_udhi={max_price}"
    
    try:
        driver.get(url)
        
        # --- 4. 模拟真人：随机等待并滚动页面 ---
        print("DEBUG: 模拟真人行为中...")
        time.sleep(random.uniform(2, 4)) 
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
        time.sleep(1)

        # 5. ⏳ 等待商品列表加载
        print("DEBUG: 正在搜索商品节点...")
        wait = WebDriverWait(driver, 15) # 增加到 15 秒，给校园网一点缓冲
        
        # eBay 的商品标题通常在 .s-item__title 
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".s-item__title")))

        # 6. 🔍 抓取所有商品块
        # 使用更稳健的 CSS 选择器，排除掉非商品块
        items_elements = driver.find_elements(By.CSS_SELECTOR, ".s-item__wrapper")
        
        print(f"DEBUG: 页面上一共找到了 {len(items_elements)} 个商品块")

        items = []
        for el in items_elements:
            try:
                # 在块内提取标题
                title_el = el.find_element(By.CSS_SELECTOR, ".s-item__title")
                # 排除掉 "New Listing" 等干扰标签
                title = title_el.text.replace("New Listing", "").strip()
                
                if not title or "Shop on eBay" in title:
                    continue

                # 提取价格
                price_el = el.find_element(By.CSS_SELECTOR, ".s-item__price")
                raw_price = price_el.text
                
                # 正则提取：只拿数字和点，处理 "AU $1,234.56 to ..." 情况
                price_match = re.search(r"[\d,.]+", raw_price.replace(",", ""))
                if price_match:
                    price = float(price_match.group())
                else:
                    continue
                
                # 提取链接
                link_el = el.find_element(By.CSS_SELECTOR, ".s-item__link")
                link = link_el.get_attribute("href")

                items.append({
                    'title': title,
                    'price': price,
                    'link': link
                })
            except Exception:
                continue

    except Exception as e:
        print(f"❌ 抓取出错: {e}")
        # 如果出错，截个图看看是不是验证码
        driver.save_screenshot("error_debug.png")
        print("DEBUG: 已保存错误截图 error_debug.png，请查看是否出现了验证码")
    finally:
        driver.quit()

    return items
    