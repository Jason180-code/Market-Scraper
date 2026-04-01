import requests
from bs4 import BeautifulSoup

def scrape_ebay(keywords, max_price):
    # 替换为澳洲站，增加搜索参数
    url = f"https://www.ebay.com.au/sch/i.html?_nkw={keywords}&_udhi={max_price}"
    
    # 模拟浏览器访问，非常重要！
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        # timeout 改为 20，给网络留点余地
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        items = []
        
        # 这里需要确保你的 BeautifulSoup 提取逻辑与 eBay 澳洲站的 HTML 结构匹配
        # (通常 eBay 各站点的结构是类似的)
        for result in soup.select('.s-item__info')[:10]: # 只取前10个测试
            title = result.select_one('.s-item__title')
            price = result.select_one('.s-item__price')
            link = result.select_one('.s-item__link')
            
            if title and price and link:
                items.append({
                    'title': title.text.replace("New Listing", "").strip(),
                    'price': float(price.text.replace('$', '').replace(',', '').split()[0]),
                    'link': link['href']
                })
        return items

    except Exception as e:
        print(f"爬取过程中出现错误: {e}")
        return []