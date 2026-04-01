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
        # 给页面更多的呼吸时间，有时候 eBay 渲染很慢
        time.sleep(5) 
        
        # 1. 强制刷新 DOM 状态 (有些页面是异步加载的)
        print("DEBUG: 正在深度扫描页面结构...")
        
        # 2. 【最强模糊查找】：寻找所有包含 s-item 的元素，不管是 li, div 还是 section
        elements = driver.find_elements(By.XPATH, "//*[contains(@class, 's-item')]")
        
        # 3. 如果还是 0，尝试直接抓取所有 <h3>，因为商品标题几乎全是 <h3>
        if len(elements) < 3:
            print("DEBUG: 常规节点失效，尝试标题注入模式...")
            # 向上溯源：从 h3 标题往上找它的父容器
            h3_titles = driver.find_elements(By.TAG_NAME, "h3")
            elements = [h.find_element(By.XPATH, "./..") for h in h3_titles if len(h.text) > 10]

        print(f"🔍 最终定位到了 {len(elements)} 个潜在节点")

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