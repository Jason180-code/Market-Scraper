import re
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_ebay(keywords, max_price):
    # 1. 配置 Edge 选项
    edge_options = Options()
    # 稳定后可以取消下面这行的注释，开启无头模式（不弹窗）
    # edge_options.add_argument("--headless") 
    edge_options.add_argument("--disable-gpu")
    # 这一行非常重要：隐藏 Selenium 的自动化特征
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    edge_options.add_experimental_option('useAutomationExtension', False)
    
    # 禁用日志输出，减少干扰
    edge_options.add_argument("--log-level=3")
    edge_options.add_argument("--silent")
    
    # 伪装一个更现代的 UA
    edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0")

    # 2. 初始化驱动 (指向你手动下载的路径)
    service = Service(executable_path=r"E:\MarketPachong\msedgedriver.exe")
    driver = webdriver.Edge(service=service, options=edge_options)

    url = f"https://www.ebay.com.au/sch/i.html?_nkw={keywords}&_udhi={max_price}&_sop=12"
    
    items = []
    try:
        print(f"DEBUG: 正在打开页面并等待渲染: {url}")
        driver.get(url)
        
        # 3. 显式等待：直到页面上出现了商品标题 (最多等 15 秒)
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "s-item__title"))
            )
        except:
            print("DEBUG: 等待超时，可能页面加载太慢或类名变了")

        # 4. 模拟向下滑动，触发懒加载内容
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(2)

        # 5. 开始解析
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # 打印一下现在抓到的网页标题
        print(f"DEBUG: 当前页面标题是 -> {driver.title}")
        
        # 1. 核心修改：eBay 真正的商品都在 <li> 标签里，类名通常包含 s-item
        # 我们寻找所有类名中包含 s-item 的 li 标签
        results = soup.find_all('li', class_=re.compile(r's-item', re.I))
        
        # 如果 li 没找到，再退回到搜索 div (保底方案)
        if len(results) < 5:
            results = soup.find_all('div', class_=re.compile(r's-item__info', re.I))

        print(f"DEBUG: 终于找到了 {len(results)} 个潜在商品块")

        items = []
        for result in results:
            try:
                # 2. 提取标题：在 li 下面寻找具有特定类名的 div
                title_node = result.select_one('.s-item__title')
                if not title_node:
                    continue
                
                title_text = title_node.get_text(strip=True)
                # 过滤掉广告占位符和无关文本
                if "Shop on eBay" in title_text or not title_text:
                    continue
                
                title = title_text.replace("New Listing", "")

                # 3. 提取价格
                price_node = result.select_one('.s-item__price')
                if not price_node: 
                    continue
                
                price_text = price_node.get_text(strip=True)
                # 处理类似 "AU $1,099.00" 的字符串
                price_parts = price_text.replace('AU', '').replace('$', '').replace(',', '').strip().split()
                # 取最后一段（防止有原价干扰）
                current_price = float(re.findall(r"[-+]?\d*\.\d+|\d+", price_parts[-1])[0])

                # 4. 提取链接
                link_node = result.select_one('.s-item__link')
                if not link_node: 
                    continue
                link = link_node['href'].split('?')[0]

                if current_price <= max_price:
                    print(f"✅ 成功提取: {title[:25]}... | 价格: {current_price}")
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
        # 必须关闭浏览器进程
        driver.quit()
        
    return items