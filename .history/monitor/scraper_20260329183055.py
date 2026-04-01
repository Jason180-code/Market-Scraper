import undetected_chromedriver as uc
import random
import time
import re
import os
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
        driver = uc.Chrome(
            options=options, 
            version_main=146  # <--- 强制指定匹配你浏览器的版本
        )
        
        # 2. 构造搜索链接 (增加过滤参数：一口价、澳洲境内、每页60条)
        url = f"https://www.ebay.com.au/sch/i.html?_nkw={keywords.replace(' ', '+')}&_udhi={max_price}&_ipg=60&LH_BIN=1&_stpos=4067&_fcid=15"
        
        print(f"📡 正在秘密访问 eBay AU...")
        driver.get(url)

        # 3. 模拟真人：随机等待并滚动，给 UQ 校园网一点缓冲时间
        wait_time = random.uniform(8, 12)
        print(f"⏳ 模拟真人观察中 ({wait_time:.1f}s)...")
        time.sleep(wait_time)
        driver.execute_script("window.scrollTo(0, 600);")
        time.sleep(2)

        # 4. 核心抓取逻辑：多维度选择器
        # 优先寻找包含 s-item 类的所有容器
        elements = driver.find_elements(By.CSS_SELECTOR, ".s-item")
        
        # 如果常规方法失效，尝试通过 XPATH 深度扫描
        if len(elements) < 5:
            elements = driver.find_elements(By.XPATH, "//div[contains(@class, 's-item__info')] | //li[contains(@class, 's-item')]")

        print(f"🔍 扫描到 {len(elements)} 个潜在商品节点")

        for el in elements:
            try:
                # --- 提取标题 ---
                # 尝试多个可能的类名
                title_nodes = el.find_elements(By.CSS_SELECTOR, ".s-item__title, .s-item__title--has-tags, h3")
                if not title_nodes: continue
                title = title_nodes[0].text.replace("New Listing", "").strip()
                if not title or "Shop on eBay" in title: continue

                # --- 提取价格 ---
                price_nodes = el.find_elements(By.CSS_SELECTOR, ".s-item__price")
                if not price_nodes: continue
                price_text = price_nodes[0].text
                # 正则只提取第一个出现的数字 (处理 AU $1,200 to $1,500)
                price_nums = re.findall(r"[\d.]+", price_text.replace(",", ""))
                if not price_nums: continue
                price = float(price_nums[0])

                # --- 提取链接 ---
                link_nodes = el.find_elements(By.CSS_SELECTOR, ".s-item__link, a.s-item__link")
                if not link_nodes: continue
                link = link_nodes[0].get_attribute("href")

                if price > 0 and link:
                    items.append({'title': title, 'price': price, 'link': link})
            except:
                continue

    except Exception as e:
        print(f"⚠️ 抓取过程异常: {e}")
        if driver:
            driver.save_screenshot("final_error.png")
    finally:
        if driver:
            driver.quit()

    print(f"✅ 抓取完成，返回 {len(items)} 条数据")
    return items