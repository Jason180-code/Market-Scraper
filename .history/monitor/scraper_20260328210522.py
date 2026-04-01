import requests
from bs4 import BeautifulSoup
import time
import random
import re

def scrape_ebay(keywords, max_price):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept-Language": "en-AU,en;q=0.9",
    }

    # 使用更加直接的搜索链接，剔除干扰参数
    url = f"https://www.ebay.com.au/sch/i.html?_nkw={keywords}&_udhi={max_price}&_ipg=60"
    
    try:
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 核心修改：使用 eBay 搜索结果最稳定的类名 's-item__info'
        results = soup.select('.s-item__info')
        print(f"DEBUG: 找到潜在商品信息块: {len(results)} 个")

        items = []
        for result in results:
            try:
                # 提取标题
                title_node = result.select_one('.s-item__title')
                if not title_node or "Shop on eBay" in title_node.text:
                    continue
                
                title = title_node.get_text(strip=True).replace("New Listing", "")
                
                # 提取价格
                price_node = result.select_one('.s-item__price')
                if not price_node: continue
                
                # 清洗价格字符串 (例如: "AU $1,200.00")
                price_text = price_node.get_text(strip=True)
                price_match = re.search(r'[\d,.]+', price_text.split()[-1])
                if not price_match: continue
                
                current_price = float(price_match.group().replace(',', ''))
                
                # 提取链接
                link_node = result.select_one('.s-item__link')
                if not link_node: continue
                link = link_node['href'].split('?')[0] # 去掉追踪后缀

                # 最终过滤
                if current_price <= max_price:
                    items.append({'title': title, 'price': current_price, 'link': link})
                    
            except Exception as e:
                print(f"DEBUG: 某项解析失败: {e}")
                continue
                
        return items

    except Exception as e:
        print(f"❌ 抓取崩溃: {e}")
        return []