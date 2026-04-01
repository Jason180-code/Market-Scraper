from selenium import webdriver
from selenium.webdriver.edge.service import Service  # 修改这里
from selenium.webdriver.edge.options import Options  # 修改这里
from webdriver_manager.microsoft import EdgeChromiumDriverManager # 修改这里
from bs4 import BeautifulSoup
import time
import re

def scrape_ebay(keywords, max_price):
    # 1. 配置 Edge 选项
    edge_options = Options()
    edge_options.add_argument("--headless") 
    edge_options.add_argument("--disable-gpu")
    edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # 2. 自动下载并初始化 Edge 驱动
    # 这一行会自动帮你搞定所有路径问题
    service = Service(EdgeChromiumDriverManager().install())
    driver = webdriver.Edge(service=service, options=edge_options)
    
    url = f"https://www.ebay.com.au/sch/i.html?_nkw={keywords}&_udhi={max_price}&_sop=12"
    
    items = []
    try:
        print(f"DEBUG: 正在通过 Edge 浏览器打开: {url}")
        driver.get(url)
        
        # 3. 等待 JavaScript 加载（eBay 列表渲染需要时间）
        time.sleep(5) 
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 4. 提取逻辑
        results = soup.select('.s-item__info')
        print(f"DEBUG: Edge 渲染后找到了 {len(results)} 个商品块")

        for result in results:
            try:
                title_node = result.select_one('.s-item__title')
                if not title_node or "Shop on eBay" in title_node.text:
                    continue
                
                title = title_node.get_text(strip=True).replace("New Listing", "")
                
                price_node = result.select_one('.s-item__price')
                if not price_node: continue
                
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
        print(f"❌ Edge 运行出错: {e}")
    finally:
        # 必须关闭，否则后台会堆积 msedgewebview2.exe 进程
        driver.quit()
        
    return items