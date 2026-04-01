from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import re

def scrape_ebay(keywords, max_price):
    # 1. 配置 Chrome 选项
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 静默运行
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    # 伪装正常的 User-Agent
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # 2. 初始化驱动（第一次运行会自动下载驱动，请稍等）
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # 构造 URL
    url = f"https://www.ebay.com.au/sch/i.html?_nkw={keywords}&_udhi={max_price}&_sop=12"
    
    items = []
    try:
        print(f"DEBUG: 正在通过真实浏览器打开: {url}")
        driver.get(url)
        
        # 3. 关键：等待页面加载 JavaScript
        time.sleep(5) 
        
        # 将渲染后的页面传给 BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 4. 提取逻辑（使用最稳健的类名）
        results = soup.select('.s-item__info')
        print(f"DEBUG: Selenium 渲染后找到了 {len(results)} 个商品块")

        for result in results:
            try:
                title_node = result.select_one('.s-item__title')
                if not title_node or "Shop on eBay" in title_node.text:
                    continue
                
                title = title_node.get_text(strip=True).replace("New Listing", "")
                
                price_node = result.select_one('.s-item__price')
                if not price_node: continue
                
                # 清洗价格逻辑
                price_text = price_node.get_text(strip=True)
                price_match = re.search(r'[\d,.]+', price_text.split()[-1])
                if not price_match: continue
                
                current_price = float(price_match.group().replace(',', ''))
                
                link_node = result.select_one('.s-item__link')
                if not link_node: continue
                link = link_node['href'].split('?')[0]

                if current_price <= max_price:
                    items.append({
                        'title': title,
                        'price': current_price,
                        'link': link
                    })
            except Exception:
                continue
                
    except Exception as e:
        print(f"❌ Selenium 运行出错: {e}")
    finally:
        # 5. 必须关闭浏览器，否则后台会留下一堆进程耗尽你的内存
        driver.quit()
        
    return items