import time
import random
import re
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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