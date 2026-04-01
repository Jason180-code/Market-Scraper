import time
import random
import re
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_ebay(keywords, max_price):
    edge_options = Options()
    # --- 1. 核心伪装：移除自动化标记 ---
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    edge_options.add_experimental_option('useAutomationExtension', False)
    
    # --- 2. 避免被检测为 Headless (即使你现在开着窗口) ---
    edge_options.add_argument("--disable-blink-features=AutomationControlled")
    edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0")

    service = Service(executable_path=r"E:\MarketPachong\msedgedriver.exe")
    driver = webdriver.Edge(service=service, options=edge_options)

    # --- 3. 注入更强大的指纹抹除脚本 ---
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    # 1. 构造 URL
    url = f"https://www.ebay.com.au/sch/i.html?_nkw={keywords.replace(' ', '+')}&_udhi={max_price}"
    
    try:
        driver.get(url)
        
        # --- 4. 模拟真人：随机等待并滚动页面 ---
        print("DEBUG: 模拟真人行为中...")
        time.sleep(random.uniform(2, 4)) 
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
        time.sleep(1)

        # 5. ⏳ 等待商品列表加载
        print("DEBUG: 正在搜索商品节点...")
        wait = WebDriverWait(driver, 15) # 增加到 15 秒，给校园网一点缓冲
        
        # eBay 的商品标题通常在 .s-item__title 
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".s-item__title")))

        # 6. 🔍 抓取所有商品块
        # 使用更稳健的 CSS 选择器，排除掉非商品块
        items_elements = driver.find_elements(By.CSS_SELECTOR, ".s-item__wrapper")
        
        print(f"DEBUG: 页面上一共找到了 {len(items_elements)} 个商品块")

        items = []
        for el in items_elements:
            try:
                # 在块内提取标题
                title_el = el.find_element(By.CSS_SELECTOR, ".s-item__title")
                # 排除掉 "New Listing" 等干扰标签
                title = title_el.text.replace("New Listing", "").strip()
                
                if not title or "Shop on eBay" in title:
                    continue

                # 提取价格
                price_el = el.find_element(By.CSS_SELECTOR, ".s-item__price")
                raw_price = price_el.text
                
                # 正则提取：只拿数字和点，处理 "AU $1,234.56 to ..." 情况
                price_match = re.search(r"[\d,.]+", raw_price.replace(",", ""))
                if price_match:
                    price = float(price_match.group())
                else:
                    continue
                
                # 提取链接
                link_el = el.find_element(By.CSS_SELECTOR, ".s-item__link")
                link = link_el.get_attribute("href")

                items.append({
                    'title': title,
                    'price': price,
                    'link': link
                })
            except Exception:
                continue

    except Exception as e:
        print(f"❌ 抓取出错: {e}")
        # 如果出错，截个图看看是不是验证码
        driver.save_screenshot("error_debug.png")
        print("DEBUG: 已保存错误截图 error_debug.png，请查看是否出现了验证码")
    finally:
        driver.quit()

    return items
    edge_options = Options()
    edge_options.add_argument("--disable-gpu")
    # 进一步伪装：禁用闪烁的自动化提示
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    edge_options.add_experimental_option('useAutomationExtension', False)
    edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0")

    service = Service(executable_path=r"E:\MarketPachong\msedgedriver.exe")
    driver = webdriver.Edge(service=service, options=edge_options)

    # 再次抹除指纹
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    # 1. 构造 URL (确保包含关键字和价格限制)
    url = f"https://www.ebay.com.au/sch/i.html?_nkw={keywords.replace(' ', '+')}&_udhi={max_price}"
    driver.get(url)

    items = []
    try:
        # 2. ⏳ 显式等待：等待页面上任何一个商品标题出现，最多等 10 秒
        # 这比 time.sleep 更智能，加载完了立刻执行
        print("DEBUG: 正在等待页面加载...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "s-item__title"))
        )

        # 3. 🔍 使用更通用的选择器尝试抓取
        # eBay 的商品块通常在 .s-item 或 li.s-item 中
        items_elements = driver.find_elements(By.CSS_SELECTOR, "li.s-item")
        
        # 排除掉 eBay 搜索结果中那个讨厌的 "Shop on eBay" 提示块
        # 真正的商品通常从第二个开始
        print(f"DEBUG: 页面上一共找到了 {len(items_elements)} 个潜在节点")

        for el in items_elements:
            try:
                # 在每个 li 标签内寻找标题
                title_el = el.find_element(By.CLASS_NAME, "s-item__title")
                title = title_el.text.strip()
                
                # 如果标题是空的或者是“搜索提示”，跳过
                if not title or "Shop on eBay" in title:
                    continue

                # 寻找价格
                price_el = el.find_element(By.CLASS_NAME, "s-item__price")
                price_text = price_el.text.replace("AU ", "").replace("$", "").replace(",", "").strip()
                
                # 处理区间价格 "1200.00 to 1500.00"
                if " to " in price_text:
                    price_text = price_text.split(" to ")[0]
                
                price = float(price_text)
                
                # 寻找链接
                link_el = el.find_element(By.CLASS_NAME, "s-item__link")
                link = link_el.get_attribute("href")

                items.append({
                    'title': title,
                    'price': price,
                    'link': link
                })
            except Exception:
                # 某个节点抓不到 title 或 price 很正常（可能是广告），直接跳过
                continue

    except Exception as e:
        print(f"❌ 抓取过程中发生错误: {e}")
    finally:
        driver.quit()

    return items