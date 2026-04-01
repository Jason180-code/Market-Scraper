import undetected_chromedriver as uc
import random
import time
import re
from selenium.webdriver.common.by import By

def scrape_ebay(keywords, max_price):
    items = []
    
    # --- 1. 初始化伪装浏览器 ---
    options = uc.ChromeOptions()
    # 调试建议：先不要开 headless (无头模式)，亲眼看看它打开了什么页面
    # options.add_argument('--headless') 
    
    # 强制澳洲站点语言和地区
    options.add_argument('--lang=en-AU')
    
    try:
        # 使用 uc 直接创建驱动，它会自动处理版本匹配
        driver = uc.Chrome(
            options=options, 
            version_main=146,  # <--- 关键：手动对齐你的浏览器版本
            # browser_executable_path=edge_path # 如果是 Edge 就加上这行
        )
        
        # 2. 构造 URL (增加分页限制，让它看起来更像正常搜索)
        url = f"https://www.ebay.com.au/sch/i.html?_nkw={keywords.replace(' ', '+')}&_udhi={max_price}&_ipg=60"
        
        print(f"DEBUG: 正在访问 {url}")
        driver.get(url)
        
        # 3. ⏳ 关键：模拟人类的随机观察时间
        # eBay 会检测页面加载后，鼠标是否移动，是否等待了渲染
        time.sleep(random.uniform(6, 10)) 
        
        # 模拟向下滚动一点点
        driver.execute_script("window.scrollTo(0, 400);")
        time.sleep(2)

        # 4. 🔍 使用更底层的 XPATH 寻找商品
        # 这个 XPATH 匹配任何包含 s-item 类的 li 标签
        nodes = driver.find_elements(By.XPATH, "//li[contains(@class, 's-item')]")
        print(f"DEBUG: UC 模式成功抓取到了 {len(nodes)} 个原始节点")

        for el in nodes:
            try:
                # 提取标题
                title_els = el.find_elements(By.CSS_SELECTOR, ".s-item__title")
                if not title_els: continue
                title = title_els[0].text.replace("New Listing", "").strip()
                
                # 排除干扰
                if not title or "Shop on eBay" in title: continue

                # 提取价格
                price_els = el.find_elements(By.CSS_SELECTOR, ".s-item__price")
                if not price_els: continue
                price_text = price_els[0].text
                
                # 正则只拿第一个数字（应对区间价格）
                price_numbers = re.findall(r"[\d.]+", price_text.replace(",", ""))
                if not price_numbers: continue
                price = float(price_numbers[0])

                # 提取链接
                link_els = el.find_elements(By.CSS_SELECTOR, ".s-item__link")
                if not link_els: continue
                link = link_els[0].get_attribute("href")

                if price > 0:
                    items.append({'title': title, 'price': price, 'link': link})
                    
            except Exception:
                continue

    except Exception as e:
        print(f"❌ 终极抓取失败: {e}")
        # 即使失败也存个图，看看是不是被封 IP 了
        if 'driver' in locals():
            driver.save_screenshot("final_check.png")
    finally:
        if 'driver' in locals():
            driver.quit()

    return items