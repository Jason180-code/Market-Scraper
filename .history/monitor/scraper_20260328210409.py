import requests
from bs4 import BeautifulSoup
import time
import random
import re

def scrape_ebay(keywords, max_price):
    # 模拟真实 Chrome 浏览器的请求头
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-AU,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }

    url = f"https://www.ebay.com.au/sch/i.html?_nkw={keywords}&_udhi={max_price}&_sop=12"
    
    try:
        session = requests.Session()
        time.sleep(random.uniform(1, 3))
        response = session.get(url, headers=headers, timeout=20)
        
        if response.status_code == 503:
            print("❌ eBay 触发了反爬保护 (503)。")
            return []
            
        response.raise_for_status()
        
        # --- 调试：如果还是 0，这个文件可以告诉我们 eBay 到底给没给你数据 ---
        # with open("debug_ebay.html", "w", encoding='utf-8') as f:
        #     f.write(response.text)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 匹配包含 s-item 的所有 div
        results = soup.find_all('div', class_=lambda x: x and 's-item' in x)
        print(f"DEBUG: 页面上一共找到了 {len(results)} 个商品块")

        items = []
        for result in results[1:20]: # 扩大搜索范围到前 20 个
            try:
                title_node = result.find(['div', 'h3'], class_='s-item__title')
                price_node = result.find('span', class_='s-item__price')
                link_node = result.find('a', class_='s-item__link')
                
                if title_node and price_node and link_node:
                    title = title_node.get_text(strip=True).replace("New Listing", "")
                    price_text = price_node.get_text(strip=True)
                    
                    # 提取价格数字逻辑
                    price_digits = re.sub(r'[^\d.]', '', price_text.split()[-1])
                    if not price_digits: continue
                    current_price = float(price_digits)
                    
                    if current_price <= max_price:
                        items.append({
                            'title': title,
                            'price': current_price,
                            'link': link_node['href']
                        })
            except Exception:
                continue
                
        return items

    except Exception as e:
        print(f"❌ 抓取函数发生崩溃: {e}")
        return [] # 这里就是你之前缺失的 except 块