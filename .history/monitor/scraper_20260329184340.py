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
        driver = uc.Chrome(options=options, version_main=146)
        driver.maximize_window() 
        
        # 1. 先构造 URL 并访问
        random_suffix = uuid.uuid4().hex[:6]
        url = f"https://www.ebay.com.au/sch/i.html?_nkw={keywords.replace(' ', '+')}&_udhi={max_price}&_ipg=60&_seed={random_suffix}&LH_BIN=1"
        
        print(f"📡 正在秘密访问 eBay AU...")
        driver.get(url)

        # 2. 访问后再等待加载
        print("⏳ 页面已打开，正在模拟人类观察并等待加载...")
        time.sleep(random.uniform(10, 15)) 
        
        # 3. 模拟人类缓慢滚动 (这是关键，触发懒加载)
        for i in range(4):
            scroll_dist = random.randint(400, 800)
            driver.execute_script(f"window.scrollBy(0, {scroll_dist});")
            print(f"滚动中... {i+1}/4")
            time.sleep(random.uniform(1.5, 3.0))

        # 4. 再次确保滚动回到稍上方，通常商品列表就在这
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(3)

        print("DEBUG: 正在深度扫描页面结构...")
        
        # 5. 【暴力抓取】：不再迷信 ID，直接抓取页面上所有看起来像价格和标题的组合
        # 我们先抓取所有的商品大容器
        containers = driver.find_elements(By.CSS_SELECTOR, ".s-item__wrapper, .s-item__info")
        
        if not containers:
            # 备选方案：抓取所有的 li
            containers = driver.find_elements(By.XPATH, "//li[contains(@class, 's-item')]")

        print(f"🔍 最终定位到了 {len(containers)} 个潜在节点")

        for el in containers:
            try:
                # 在容器内寻找标题
                t_els = el.find_elements(By.CSS_SELECTOR, ".s-item__title, h3")
                if not t_els: continue
                full_title = t_els[0].text.replace("New Listing", "").strip()
                
                # 在容器内寻找价格
                p_els = el.find_elements(By.CSS_SELECTOR, ".s-item__price")
                if not p_els: continue
                p_text = p_els[0].text
                p_nums = re.findall(r"[\d.]+", p_text.replace(",", ""))
                
                # 在容器内寻找链接
                l_els = el.find_elements(By.TAG_NAME, "a")
                link = l_els[0].get_attribute("href") if l_els else ""

                if full_title and p_nums and link:
                    price_val = float(p_nums[0])
                    # 打印一下，让我们在控制台看到成果
                    if "iphone" in full_title.lower():
                        print(f"✨ 发现匹配: {full_title[:30]}... | ${price_val}")
                        items.append({'title': title, 'price': price_val, 'link': link})
            except:
                continue

        driver = uc.Chrome(
            options=options, 
            version_main=146  # <--- 强制指定匹配你浏览器的版本
        )

        # 在 driver = uc.Chrome(...) 之后添加
        driver.maximize_window() 
        
        # ... driver.get(url) 之后 ...
        print("📡 正在等待页面彻底加载...")
        time.sleep(random.uniform(10, 15)) # 增加等待时间
        
        # 模拟人类缓慢滚动（分段滚动）
        for i in range(3):
            driver.execute_script(f"window.scrollBy(0, {random.randint(300, 700)});")
            time.sleep(1)
        
        # 2. 构造搜索链接 (增加过滤参数：一口价、澳洲境内、每页60条)
        random_suffix = uuid.uuid4().hex[:6]
        url = f"https://www.ebay.com.au/sch/i.html?_nkw={keywords.replace(' ', '+')}&_udhi={max_price}&_ipg=60&_seed={random_suffix}"
        
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
                # --- 1. 标题提取 (更广泛的匹配) ---
                title = ""
                # 尝试 h3, 尝试带 title 类的 span，尝试 a 标签
                title_els = el.find_elements(By.CSS_SELECTOR, "h3, .s-item__title, .s-item__inner a")
                for t_el in title_els:
                    if t_el.text.strip():
                        title = t_el.text.replace("New Listing", "").strip()
                        break
                
                if not title or "Shop on eBay" in title or len(title) < 10:
                    continue

                # --- 2. 价格提取 (处理各种货币符号和空格) ---
                price = 0
                price_els = el.find_elements(By.CSS_SELECTOR, ".s-item__price, .s-item__details span")
                for p_el in price_els:
                    p_text = p_el.text
                    # 匹配任何带数字的部分
                    price_nums = re.findall(r"[\d,.]+", p_text.replace(",", ""))
                    if price_nums:
                        price = float(price_nums[0])
                        break

                # --- 3. 链接提取 (找最近的 href) ---
                link = ""
                link_els = el.find_elements(By.CSS_SELECTOR, "a.s-item__link, .s-item__image a, a")
                if link_els:
                    link = link_els[0].get_attribute("href")

                # --- 4. 调试输出：看看我们到底抓到了什么 ---
                if title:
                    print(f"📡 抓取测试: {title[:20]}... | Price: {price} | Link: {'Yes' if link else 'No'}")

                if price > 0 and link:
                    items.append({'title': title, 'price': price, 'link': link})
            except Exception as e:
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