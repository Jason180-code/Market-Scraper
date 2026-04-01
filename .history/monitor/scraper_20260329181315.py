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
    # 1. 变量初始化（放在最外面，防止 UnboundLocalError）
    items = [] 
    
    edge_options = Options()
    # 调试建议：暂时注释掉 headless，亲眼看看浏览器在干嘛
    # edge_options.add_argument("--headless") 
    edge_options.add_argument("--disable-blink-features=AutomationControlled")
    edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0")

    service = Service(executable_path=r"E:\MarketPachong\msedgedriver.exe")
    driver = webdriver.Edge(service=service, options=edge_options)

    try:
        # 1. 构造 URL
        url = f"https://www.ebay.com.au/sch/i.html?_nkw={keywords.replace(' ', '+')}&_udhi={max_price}"
        driver.get(url)
        
        # 2. 模拟人类操作：多等一会，并滚动一下
        print("DEBUG: 正在等待页面渲染...")
        time.sleep(5)  # 简单粗暴地等 5 秒，确保内容出来
        driver.execute_script("window.scrollTo(0, 500);") 
        
        # 3. 循环尝试抓取（最多尝试 3 次）
        items_elements = []
        for attempt in range(3):
            items_elements = driver.find_elements(By.CSS_SELECTOR, "li.s-item")
            # 排除掉只有 1-2 个节点的情况（那通常是 header）
            if len(items_elements) > 5: 
                break
            print(f"DEBUG: 尝试第 {attempt+1} 次抓取，目前只找到 {len(items_elements)} 个，继续等待...")
            time.sleep(2)

        print(f"DEBUG: 最终页面上一共找到了 {len(items_elements)} 个 li 节点")

        for el in items_elements:
            try:
                # 使用非常宽松的选择器提取
                # 标题
                title_nodes = el.find_elements(By.CSS_SELECTOR, ".s-item__title")
                if not title_nodes: continue
                title = title_nodes[0].text.replace("New Listing", "").strip()
                
                if not title or "Shop on eBay" in title: continue

                # 价格
                price_nodes = el.find_elements(By.CSS_SELECTOR, ".s-item__price")
                if not price_nodes: continue
                price_text = price_nodes[0].text
                
                # 提取数字
                price_numbers = re.findall(r"[\d.]+", price_text.replace(",", ""))
                price = float(price_numbers[0]) if price_numbers else 0

                # 链接
                link_nodes = el.find_elements(By.CSS_SELECTOR, ".s-item__link")
                if not link_nodes: continue
                link = link_nodes[0].get_attribute("href")

                if price > 0:
                    items.append({'title': title, 'price': price, 'link': link})
            except Exception:
                continue

        except Exception as e:
            print(f"❌ 抓取逻辑崩溃: {e}")
        # 2. 执行抓取
        url = f"https://www.ebay.com.au/sch/i.html?_nkw={keywords.replace(' ', '+')}&_udhi={max_price}"
        driver.get(url)
        
        # ⏳ 显式等待：等待标题出现
        wait = WebDriverWait(driver, 15)
        print("DEBUG: 正在等待页面渲染...")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".s-item__title")))

        # 🔍 核心修改：使用更宽泛的 li 选择器
        # eBay 的每个商品（无论是列表还是网格）都在一个带 .s-item 的 li 标签里
        items_elements = driver.find_elements(By.CSS_SELECTOR, "li.s-item")
        print(f"DEBUG: 页面上一共找到了 {len(items_elements)} 个 li 节点")

        items = []
        for el in items_elements:
            try:
                # 1. 提取标题 (使用类名中包含的部分匹配，更稳)
                title_el = el.find_element(By.CSS_SELECTOR, ".s-item__title")
                title = title_el.text.replace("New Listing", "").strip()
                
                # 排除搜索结果外的干扰项
                if not title or "Shop on eBay" in title:
                    continue

                # 2. 提取价格
                price_el = el.find_element(By.CSS_SELECTOR, ".s-item__price")
                price_text = price_el.text
                
                # 💡 这里的正则非常关键：它会匹配第一个数字（处理 "5.85 to 11.45" 这种情况）
                # 我们只关心最低价是否符合你的 1000-2000 要求
                price_numbers = re.findall(r"[\d.]+", price_text.replace(",", ""))
                if price_numbers:
                    price = float(price_numbers[0])
                else:
                    continue

                # 3. 提取链接
                link_el = el.find_element(By.CSS_SELECTOR, ".s-item__link")
                link = link_el.get_attribute("href")

                # 只要抓到了基本信息，就存入列表
                items.append({
                    'title': title,
                    'price': price,
                    'link': link
                })
            except Exception:
                # 广告位或者结构不全的直接跳过，不报错
                continue

    except Exception as e:
        print(f"❌ 抓取出错: {e}")
        driver.save_screenshot("error_debug.png") # 记录案发现场
    finally:
        driver.quit()

    return items # 此时即使报错，也能返回 []，不会再报 UnboundLocalError