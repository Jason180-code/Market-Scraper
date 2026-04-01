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
        print(f"DEBUG: 正在直接操作浏览器内核: {url}")
        driver.get(url)
        
        # 1. 深度等待：确保商品块渲染出来
        wait = WebDriverWait(driver, 20)
        # eBay 澳洲站列表项的通用 CSS 路径
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".s-item")))
        
        # 2. 模拟真人：慢慢滚动到底部，再滚回来，触发所有懒加载
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 2000);")
        time.sleep(1)

        # 3. 【核心修改】直接用 driver 找元素，不通过 BeautifulSoup
        # 寻找所有类名包含 s-item 的元素
        product_elements = driver.find_elements(By.CSS_SELECTOR, "li.s-item")
        print(f"DEBUG: 浏览器内核直接反馈找到了 {len(product_elements)} 个商品块")

        for el in product_elements:
            try:
                # 在每个块内寻找标题
                title_el = el.find_element(By.CSS_SELECTOR, ".s-item__title")
                title = title_el.text.replace("New Listing", "").strip()
                
                if not title or "Shop on eBay" in title:
                    continue

                # 寻找价格
                price_el = el.find_element(By.CSS_SELECTOR, ".s-item__price")
                price_text = price_el.text
                
                # 正则处理价格
                price_nums = re.findall(r"[\d,.]+", price_text.replace(',', ''))
                if not price_nums: continue
                current_price = float(price_nums[-1])

                # 寻找链接
                link_el = el.find_element(By.TAG_NAME, "a")
                link = link_el.get_attribute("href").split('?')[0]

                if current_price <= max_price:
                    print(f"✅ 捕获成功: {title[:20]}... | ${current_price}")
                    items.append({'title': title, 'price': current_price, 'link': link})
            except:
                continue

    except Exception as e:
        print(f"❌ 运行异常: {e}")
    finally:
        driver.quit()
        
    return items