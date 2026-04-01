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
        # 强制指定版本并启动
        driver = uc.Chrome(options=options, version_main=146)
        driver.maximize_window()
        
        # 2. 构造干净的 URL (LH_BIN=1 是“一口价”，能避开拍卖行的复杂结构)
        url = f"https://www.ebay.com.au/sch/i.html?_nkw={keywords.replace(' ', '+')}&_udhi={max_price}&LH_BIN=1&_ipg=60"
        
        print(f"📡 正在秘密访问: {url}")
        driver.get(url)

        # 3. 充分等待加载
        print("⏳ 等待页面渲染中...")
        time.sleep(12) 
        
        # 4. 模拟人类滚动（这是触发数据加载的关键）
        for i in range(3):
            driver.execute_script(f"window.scrollBy(0, {random.randint(500, 800)});")
            time.sleep(2)

        # 5. 【暴力提取法】：不找具体的 Class，直接找所有带有价格特征的文本块
        print("DEBUG: 正在进行全网页深度扫描...")
        
        # 尝试寻找所有包含“AU $”或者数字的价格标签
        # 这里的 XPath 逻辑是：找到包含价格的元素，然后往上找它的父容器
        potential_items = driver.find_elements(By.XPATH, "//*[contains(text(), '$')]//ancestor::div[contains(@class, 's-item__info') or contains(@class, 's-item__wrapper')]")

        if not potential_items:
            # 最后的倔强：直接找所有的 li 标签
            potential_items = driver.find_elements(By.CSS_SELECTOR, "li.s-item")

        print(f"🔍 最终探测到 {len(potential_items)} 个商品区块")

        for el in potential_items:
            try:
                # 提取标题：通常在 h3 
                t_els = el.find_elements(By.TAG_NAME, "h3")
                if not t_els: continue
                title_text = t_els[0].text.strip()
                
                # 提取价格：正则表达式匹配数字
                p_els = el.find_elements(By.CSS_SELECTOR, ".s-item__price")
                if not p_els: continue
                p_nums = re.findall(r"[\d,.]+", p_els[0].text.replace(",", ""))
                
                # 提取链接
                l_els = el.find_elements(By.TAG_NAME, "a")
                link = l_els[0].get_attribute("href") if l_els else ""

                if title_text and p_nums and link:
                    price_val = float(p_nums[0])
                    # 只要包含关键词就收割
                    if "iphone" in title_text.lower():
                        items.append({'title': title_text, 'price': price_val, 'link': link})
                        print(f"✨ 成功捕获: {title_text[:25]}... | ${price_val}")
            except:
                continue

    except Exception as e:
        print(f"❌ 运行异常: {e}")
        if driver: driver.save_screenshot("final_debug.png")
    finally:
        if driver: driver.quit()

    return items
     