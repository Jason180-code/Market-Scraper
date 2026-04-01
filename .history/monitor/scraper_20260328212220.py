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

    # --- 关键修改：不再使用 EdgeChromiumDriverManager ---
    # 直接指向你刚刚放进项目根目录的 exe 文件
    service = Service(executable_path=r"E:\MarketPachong\msedgedriver.exe")
    driver = webdriver.Edge(service=service, options=edge_options)
    # -----------------------------------------------

    url = f"https://www.ebay.com.au/sch/i.html?_nkw={keywords}&_udhi={max_price}&_sop=12"
    
    items = []
    try:
        print(f"DEBUG: 正在通过 Edge 浏览器打开: {url}")
        driver.get(url)
        
        # 3. 等待 JavaScript 加载（eBay 列表渲染需要时间）
        # 3. 增加等待时间，并模拟滚动（让 eBay 觉得是真人在翻页）
        time.sleep(8) 
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 4. 更加“暴力”的选择器：匹配任何包含 s-item 关键词的容器
        results = soup.find_all('div', class_=re.compile(r's-item__info|s-item__wrapper'))
        print(f"DEBUG: Edge 渲染后找到了 {len(results)} 个潜在商品块")

        # 如果还是 0，打印前 500 个字符看看网页到底给了什么

if len(results) == 0:
            print("DEBUG: 网页内容前500字:", soup.get_text()[:500])
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