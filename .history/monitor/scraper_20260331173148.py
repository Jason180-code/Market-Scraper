import time
import random
import re
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_ebay(keywords, max_price, min_price=100):
    edge_options = Options()
    edge_options.add_argument("--disable-gpu")
    # 进一步伪装：禁用闪烁的自动化提示
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    edge_options.add_experimental_option('useAutomationExtension', False)
    edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0")

    service = Service(executable_path=r"E:\MarketPachong\msedgedriver.exe")
    driver = webdriver.Edge(service=service, options=edge_options)

    # 再次抹除指纹
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {e
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    exclude_query = "-case -cover -protector -film -glass -tempered -housing -parts"
    url = f"https://www.ebay.com.au/sch/i.html?_nkw={keywords}+{exclude_query}&_udhi={max_price}&_sop=12&_sacat=9355"
    items = []

    try:
        print(f"DEBUG: 正在打开页面，请观察浏览器是否出现了验证码...")
        driver.get(url)

        # 1. 停顿更久，给你手动处理验证码的时间
        # 如果你看到验证码，请在弹出的浏览器里手动点一下
        time.sleep(5) 

        # 2. 尝试寻找页面上所有的 <li> 标签
        # 即使类名变了，商品列表通常依然是 <li> 结构
        li_elements = driver.find_elements(By.TAG_NAME, "li")
        print(f"DEBUG: 页面上一共找到了 {len(li_elements)} 个列表项")

        # 基于 image_0.png 和 image_1.png 定制的强力黑名单
        BLACK_LIST = [
            # --- 1. 配件与周边 (Accessories & Perimeter) ---
            "case", "cover", "bag", "pouch", "sleeve", "skin", "sticker", "decal",
            "protector", "film", "tempered", "glass", "lens cap", "hood",
            "strap", "band", "lanyard", "keychain", "stand", "holder", "mount",
            "cable", "adapter", "charger", "plug", "converter", "dock", "hub",
            "stylus", "pen nib", "earpads", "ear tips", "filter", "silicone",

            # --- 2. 纯零件与损坏件 (Parts & Broken - 捡漏工具的天敌) ---
            "parts", "only", "broken", "faulty", "crack", "damaged", "repair",
            "not working", "as-is", "defective", "housing", "shell", "bezel",
            "screen replacement", "battery replacement", "replacement", 
            "logic board", "motherboard only", "empty box", "box only",

            # --- 3. 针对性干扰词 (The "For" Trap) ---
            "for", "suit", "fit", "compatible", "matching", "designed for",
            "compatible with", "replacement for",

            # --- 4. 材质与视觉干扰 (Materials & Junk) ---
            "silicone", "leather", "carbon fiber", "plastic", "metal", 
            "glitter", "clear", "matte", "anti-spy", "privacy",
            "cleaning kit", "tool kit", "screws", "bracket"
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
                
                #过滤逻辑 1:屏蔽以 "for iphone" 开头的标题（通常是配件）
                if title_lower.startswith("for iphone") and len(title) > 80:
                    print(f"   ❌ 被判定为长标题配件包")
                    continue
                # --- 新增过滤逻辑 2: 关键词黑名单 ---
                if any(word in title_lower for word in BLACK_LIST):
                    print(f"   ❌ 黑名单拦截: {title[:40]}")
                    continue
                
                # --- 新增过滤逻辑 3: 必须包含核心词 (防配件干扰) ---
                # 比如你要搜 iPhone，结果里没这个词的通常是乱入的
                core_keyword = keywords.split()[0].lower() 
                if core_keyword not in title_lower:
                    print(f"   ❌ 标题中不包含核心词 '{core_keyword}'")
                    continue
                
                # 提取价格：用正则找带 $ 的数字
                price_match = re.search(r'\$\s?([\d,.]+)', text_content)
                if not price_match:
                    continue
                current_price = float(price_match.group(1).replace(',', ''))
                
                # --- 新增过滤逻辑 C: 价格下限保护 ---
                # 设定一个合理的最低价。比如 iPhone 15PM 不可能低于 400 刀
                # 这里根据 keywords 动态调整或者设个通用值，比如 100
                if current_price < min_price:
                    print(f"   ❌ 价格低于下限 (${current_price})")
                    continue
                
                if any(word in title_lower for word in BLACK_LIST):
                
                # 进一步检查：被拦截的词是否是用户搜的？
                # 比如用户搜 "Case"，我们就不能因为 "case" 在黑名单里就过滤掉它
                    is_safe = False
                    for word in BLACK_LIST:
                        if word in title_lower and word not in user_keywords_list:
                            print(f"   ❌ 黑名单拦截: {word} -> {title[:30]}")
                            is_safe = False
                            break
                        else:
                            is_safe = True
    
                    if not is_safe:
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