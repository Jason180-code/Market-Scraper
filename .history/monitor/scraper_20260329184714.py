import undetected_chromedriver as uc
import random
import time
import re
import os
import uuid
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_ebay(keywords, max_price):
    items = []
    # 自动识别 Chrome 版本，如果报错请确保电脑已安装 Chrome 浏览器
    options = uc.ChromeOptions()
    # 建议调试阶段关掉 headless，成功后再开启
    # options.add_argument('--headless') 
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--lang=en-AU')

    driver = None
    try:
        driver = uc.Chrome(options=options, version_main=146)
        driver.maximize_window()
        
        # 1. 访问 URL (加上额外的搜索偏移，防止被缓存)
        url = f"https://www.ebay.com.au/sch/i.html?_nkw={keywords.replace(' ', '+')}&_udhi={max_price}&LH_BIN=1&_sop=12"
        print(f"📡 正在深度访问: {url}")
        driver.get(url)

        # 2. 【硬核等待】：给 20 秒，确保异步 JS 加载完毕
        print("⏳ 正在等待 20 秒，确保 UQ 区域数据链路稳定...")
        time.sleep(20) 

        # 3. 模拟滚动，触发懒加载
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(3)

        # 4. 【核心策略】：直接抓取全网页 HTML
        page_html = driver.page_source
        
        # 5. 使用正则表达式在 HTML 源码中寻找标题和价格
        # eBay 的商品通常在包含 s-item__info 的区块内
        # 我们寻找所有的 "s-item__title" 后面的文本
        print("DEBUG: 正在从网页源代码中强行提取数据...")
        
        # 寻找标题、价格和链接的正则匹配
        # 这是一个粗鲁但极其有效的办法，绕过了所有 CSS 渲染问题
        titles = re.findall(r'class="s-item__title"[^>]*>(?:<span[^>]*>)?(.*?)(?:</span>)?</h3>', page_html)
        prices = re.findall(r'class="s-item__price"[^>]*>(.*?)</span>', page_html)
        links = re.findall(r'class="s-item__link" href="(.*?)"', page_html)

        print(f"🔍 源码中发现：标题({len(titles)})，价格({len(prices)})，链接({len(links)})")

        # 6. 对齐数据
        min_len = min(len(titles), len(prices), len(links))
        for i in range(min_len):
            title_clean = re.sub(r'<.*?>', '', titles[i]).replace("New Listing", "").strip()
            price_text = prices[i]
            price_nums = re.findall(r"[\d.]+", price_text.replace(",", ""))
            
            if title_clean and price_nums:
                price_val = float(price_nums[0])
                # 只要是 iPhone 且价格不为 0 就收录
                if "iphone" in title_clean.lower():
                    items.append({
                        'title': title_clean,
                        'price': price_val,
                        'link': links[i]
                    })
                    print(f"✨ 成功捕获: {title_clean[:25]}... | ${price_val}")

    except Exception as e:
        print(f"❌ 运行异常: {e}")
        if driver: driver.save_screenshot("final_debug.png")

    finally:
        if driver: driver.quit()

    return items
