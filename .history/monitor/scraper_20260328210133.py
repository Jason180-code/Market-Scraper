import requests
from bs4 import BeautifulSoup
import time
import random

def scrape_ebay(keywords, max_price):
    # 模拟真实 Chrome 浏览器的请求头
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-AU,en;q=0.9",  # 模拟澳洲本地语言设置
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0",
    }

    # 尝试使用澳洲站点的搜索链接
    url = f"https://www.ebay.com.au/sch/i.html?_nkw={keywords}&_udhi={max_price}&_sop=12" # _sop=12 是按新上架排序
    
    try:
        # 使用 session 可以自动处理一些 cookie，更像真实用户
        session = requests.Session()
        
        # 随机休眠 1-3 秒，防止操作太快被封
        time.sleep(random.uniform(1, 3))
        
        response = session.get(url, headers=headers, timeout=20)
        
        if response.status_code == 503:
            print("❌ eBay 触发了反爬保护 (503)。")
            return []
            
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        # 尝试更通用的选择器：只要类名里包含 s-item 就可以
        results = soup.find_all('div', class_=lambda x: x and 's-item' in x)
        
        # 调试信息：看看一共搜到了多少个结果
        print(f"DEBUG: 页面上一共找到了 {len(results)} 个商品块")

        # eBay 的搜索结果通常在 s-item 容器中
        items = []
        
        for result in results[1:15]:  # 取前14个
          tr
           # 尝试多种可能的标题类名
                title_node = result.find(['div', 'h3'], class_='s-item__title')
                price_node = result.find('span', class_='s-item__price')
                link_node = result.find('a', class_='s-item__link')
            
            if title_node and price_node and link_node:
                title = title_node.get_text(strip=True).replace("New Listing", "")
                # 提取价格数字
                price_str = price_node.get_text(strip=True).replace('$', '').replace(',', '')
                try:
                    # 处理 "AU $123.00" 这种格式
                    current_price = float(price_str.split()[-1])
                    items.append({
                        'title': title,
                        'price': current_price,
                        'link': link_node['href']
                    })
                except:
                    continue
        return items

    except Exception as e:
        print(f"爬取过程中出现错误: {e}")
        return []