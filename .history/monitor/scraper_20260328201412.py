import requests
from bs4 import BeautifulSoup
import time

def scrape_ebay(keywords, max_price):
    # 1. 构造请求头，伪装成真实浏览器（非常重要！）
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    # 2. 构造 eBay 搜索 URL
    # _nkw: 关键词, _udhi: 最高价, _sop=10: 设置为“最新发布”排序
    url = f"https://www.ebay.com/sch/i.html?_nkw={keywords}&_udhi={max_price}&_sop=10"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # 如果请求失败则抛出异常
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 3. 找到所有商品列表容器 (eBay 的商品通常在 s-item__wrapper 类中)
        items = soup.find_all('div', class_='s-item__wrapper')
        
        results = []
        
        for item in items:
            # 提取标题
            title_tag = item.find('div', class_='s-item__title')
            title = title_tag.text.strip() if title_tag else "No Title"
            
            # 排除 eBay 搜索结果中常见的 "Shop on eBay" 干扰项
            if "Shop on eBay" in title:
                continue
                
            # 提取价格 (去掉 $ 符号并转为浮点数)
            price_tag = item.find('span', class_='s-item__price')
            price_str = price_tag.text.replace('$', '').replace(',', '').strip() if price_tag else "0"
            
            # 处理价格区间情况 (如 "$10.00 to $20.00")
            if "to" in price_str:
                price_str = price_str.split('to')[0].strip()
            
            try:
                price = float(price_str)
            except ValueError:
                price = 0.0

            # 提取链接
            link_tag = item.find('a', class_='s-item__link')
            link = link_tag['href'] if link_tag else ""

            # 提取图片
            img_tag = item.find('img')
            img_url = img_tag['src'] if img_tag else ""

            results.append({
                'title': title,
                'price': price,
                'link': link,
                'img_url': img_url
            })
            
        return results

    except Exception as e:
        print(f"爬取过程中出现错误: {e}")
        return []

# --- 测试运行 ---
if __name__ == "__main__":
    print("正在搜索价格低于 $300 的 Herman Miller 椅子...")
    found_items = scrape_ebay("Herman Miller", 300)
    
    for i, item in enumerate(found_items[:5]): # 只打印前 5 个结果
        print(f"[{i+1}] {item['title']}")
        print(f"    价格: ${item['price']}")
        print(f"    链接: {item['link'][:60]}...")