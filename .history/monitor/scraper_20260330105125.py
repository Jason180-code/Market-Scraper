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

    url = f"https://www.ebay.com.au/sch/i.html?_nkw={keywords}&_udhi={max_price}&_sop=12"
    items = []

    try:
        print(f"DEBUG: 正在打开页面，请观察浏览器是否出现了验证码...")
        driver.get(url)
        
        # 1. 停顿更久，给你手动处理验证码的时间
        # 如果你看到验证码，请在弹出的浏览器里手动点一下
        time.sleep(10) 

        # 2. 尝试寻找页面上所有的 <li> 标签
        # 即使类名变了，商品列表通常依然是 <li> 结构
        li_elements = driver.find_elements(By.TAG_NAME, "li")
        print(f"DEBUG: 页面上一共找到了 {len(li_elements)} 个列表项")

        # 基于 image_0.png 和 image_1.png 定制的强力黑名单
        BLACK_LIST = [
            # 1. 核心保护壳/盖 (Case/Cover) - 截图中最泛滥的
            "case", "cover", "housing", "shell", "skin", "bumper",
            "rugged", "shockproof", "magnetic", "magsafe case",
            "wallet", "leather flip", "card holder", "plating case",
            
            # 2. 屏幕/镜头保护 (Protector) - 第二大噪音来源
            "protector", "film", "glass", "tempered", "privacy", 
            "maxshield", "lens", "camera lens", "camera ring",
            
            # 3. 干扰性动词/介词 (防“蹭热度”)
            "for iphone", "fit for", "suit for", # 标题开头是 For 的 99% 是配件
            
            # 4. 其他配件/材质干扰
            "metal aluminium", "silicone", "clear", "glitter", 
            "spigen", "ultra hybrid", "kickstand", "stand", "ring count",
            "wallet leather", "zipper"
        ]
        
        for el in li_elements:
            try:
                # 只要这个 <li> 里面包含价格符号 '$'，我们就认为它是商品
                text_content = el.text
                if '$' not in text_content:
                    continue
                
                # 提取标题：通常是这个块里最大的文字部分
                # 或者直接取第一行
                lines = text_content.split('\n')
                title = lines[0] if "New Listing" not in lines[0] else lines[1]
                title_lower = title.lower()
                
                # --- 新增过滤逻辑 A: 关键词黑名单 ---
                if any(word in title_lower for word in BLACK_LIST):
                    continue
                
                # --- 新增过滤逻辑 B: 必须包含核心词 (防配件干扰) ---
                # 比如你要搜 iPhone，结果里没这个词的通常是乱入的
                if "iphone" not in title_lower:
                    continue
                
                #guo

                # 提取价格：用正则找带 $ 的数字
                price_match = re.search(r'\$\s?([\d,.]+)', text_content)
                if not price_match:
                    continue
                current_price = float(price_match.group(1).replace(',', ''))
                
                # --- 新增过滤逻辑 C: 价格下限保护 ---
                # 设定一个合理的最低价。比如 iPhone 15PM 不可能低于 400 刀
                # 这里根据 keywords 动态调整或者设个通用值，比如 100
                if current_price < 150: 
                    continue
                
                # 提取链接
                link_el = el.find_element(By.TAG_NAME, "a")
                link = link_el.get_attribute("href").split('?')[0]

                if current_price <= max_price:
                    print(f"✅ 捕获到商品: {title[:30]}... | ${current_price}")
                    items.append({'title': title, 'price': current_price, 'link': link})
            except:
                continue

    except Exception as e:
        print(f"❌ 运行异常: {e}")
    finally:
        driver.quit()
        
    return items