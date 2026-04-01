import re
import time
import random
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_ebay(keywords, max_price):
    edge_options = Options()
    edge_options.add_argument("--disable-gpu")
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    edge_options.add_experimental_option('useAutomationExtension', False)
    
    # 隐藏指纹的关键：伪装成普通的 Edge 浏览器
    edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0")

    service = Service(executable_path=r"E:\MarketPachong\msedgedriver.exe")
    driver = webdriver.Edge(service=service, options=edge_options)

    # 【杀招 1】利用 CDP 命令抹除 webdriver 特征，让网站认为你是真人在用
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })

    url = f"https://www.ebay.com.au/sch/i.html?_nkw={keywords}&_udhi={max_price}&_sop=12"
    
    items = []
    try:
        print(f"DEBUG: 正在加载页面: {url}")
        driver.get(url)
        
        # 【杀招 2】增加随机漫长等待，确保 JS 渲染完成
        time.sleep(random.uniform(5, 8)) 
        
        # 模拟真人向下滚动一点点
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 【杀招 3】最模糊匹配法：
        # 不再纠结特定的类名，找所有包含 's-item' 字符的 <li> 或 <div>
        all_lis = soup.find_all('li', class_=re.compile(r's-item', re.I))
        all_divs = soup.find_all('div', class_=re.compile(r's-item__info', re.I))
        
        # 合并并去重
        results = all_lis if len(all_lis) > 2 else all_divs
        print(f"DEBUG: 原始找到了 {len(results)} 个块")

        for result in results:
            try:
                # 寻找包含标题的节点 (寻找 class 包含 title 的元素)
                title_node = result.find(class_=re.compile(r'title', re.I))
                if not title_node or "Shop on eBay" in title_node.get_text():
                    continue
                
                title = title_node.get_text(strip=True).replace("New Listing", "")

                # 寻找包含价格的节点 (寻找 class 包含 price 的元素)
                price_node = result.find(class_=re.compile(r'price', re.I))
                if not price_node: continue
                
                price_text = price_node.get_text(strip=True)
                # 正则只提取最后一个数字块 (处理 AU $1,200.00 这种格式)
                nums = re.findall(r"[\d,.]+", price_text.replace(',', ''))
                if not nums: continue
                current_price = float(nums[-1])

                # 寻找链接
                link_node = result.find('a', href=True)
                if not link_node: continue
                link = link_node['href'].split('?')[0]

                if current_price <= max_price:
                    print(f"✅ 成功命中: {title[:20]}... | ${current_price}")
                    items.append({'title': title, 'price': current_price, 'link': link})
            except:
                continue
                
    except Exception as e:
        print(f"❌ 运行异常: {e}")
    finally:
        driver.quit()
        
    return items