import time
import random
import re
import os
imp
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

def scrape_ebay(keywords, max_price, min_price=100):
    """
    智能适配环境的 eBay 爬虫驱动初始化
    """
    # ✨ 关键：探测是否运行在 Docker 容器内部
    # 容器内部通常会包含 /.dockerenv 文件
    IS_DOCKER = os.path.exists('/.dockerenv')
    
    # 获取用户设置的 core 关键词（用于防配件干扰）
    user_keywords_list = keywords.lower().split()
    
    items = []
    
    # 定义通用的 UA，防止被识别为爬虫
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

    # ==========================================
    # 🚗 场景 A: 运行在 Linux 服务器 / Docker 容器内部
    # ==========================================
    if IS_DOCKER:
        print("DEBUG: 探测到 Docker 环境，启动 Chrome Headless...")
        chrome_options = ChromeOptions()
        chrome_options.add_argument("--headless=new") # 服务器必须无头
        chrome_options.add_argument("--no-sandbox")   # 容器必备参数
        chrome_options.add_argument("--disable-dev-shm-usage") # 容器必备参数
        chrome_options.add_argument(f"user-agent={user_agent}")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        # 使用 webdriver-manager 自动管理 Linux 下的 ChromeDriver
        # 这也是为什么我们需要在 requirements.txt 里加 webdriver-manager
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
    # ==========================================
    # 💻 场景 B: 运行在你本地布里斯班的 Windows 电脑上
    # ==========================================
    else:
        print("DEBUG: 探测到 Windows 本地环境，启动 Edge...")
        edge_options = EdgeOptions()
        # 本地调试可以不开启 headless 以观察效果
        # edge_options.add_argument("--headless") 
        edge_options.add_argument("--disable-gpu")
        edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        edge_options.add_experimental_option('useAutomationExtension', False)
        edge_options.add_argument(f"user-agent={user_agent}")
        
        # ✨ 本地仍然可以使用你原来的写死路径，或者也改用 manager
        # 这里为了兼容你以前的操作，我们仍用旧路径，但你可以按需修改：
        local_driver_path = r"E:\MarketPachong\msedgedriver.exe"
        if os.path.exists(local_driver_path):
            service = EdgeService(executable_path=local_driver_path)
            driver = webdriver.Edge(service=service, options=edge_options)
        else:
            # 如果本地路径找不到，也自动用 manager 下载
            service = EdgeService(EdgeChromiumDriverManager().install())
            driver = webdriver.Edge(service=service, options=edge_options)

    # 抹除指纹（对 Chrome 和 Edge 都有效）
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
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
            "card", "case", "cover", "bag", "pouch", "sleeve", "skin", "sticker", "decal",
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

# monitor/scraper.py

def scrape_facebook(keywords, max_price, min_price=100):
    IS_DOCKER = os.path.exists('/.dockerenv')
    items = []
    
    # 1. 环境适配：选择浏览器和配置路径
    if IS_DOCKER:
        print("DEBUG: FB探测到 Docker 环境，启动 Chrome...")
        options = ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # ✨ 关键：Docker 内部的路径映射（我们在 docker run 时挂载）
        user_data = "/app/user_data" 
        options.add_argument(f"user-data-dir={user_data}")
        # 注意：Linux 下 Profile 文件夹名通常就是 Default
        options.add_argument("profile-directory=Default")
        
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    else:
        print("DEBUG: FB探测到 Windows 环境，启动 Edge...")
        options = EdgeOptions()
        # options.add_argument("--headless") 
        options.add_argument("--disable-notifications")
        
        # 你原本的本地路径
        user_data = r"C:\Users\zzj20\AppData\Local\Microsoft\Edge\User Data"
        options.add_argument(f"user-data-dir={user_data}")
        options.add_argument("profile-directory=Default")
        
        local_driver_path = r"E:\MarketPachong\msedgedriver.exe"
        service = EdgeService(executable_path=local_driver_path)
        driver = webdriver.Edge(service=service, options=options)

    # 1. 核心 URL：锁定布里斯班 (Brisbane)，距离 20km 范围内
    # exact=false 表示允许模糊匹配
    base_url = "https://www.facebook.com/marketplace/brisbane/search/?"
    url = f"{base_url}query={keywords}&maxPrice={max_price}&minPrice={min_price}&exact=false"
    
    items = []
    
    try:
        driver.get(url)
        # FB 页面大，加载时间要给足
        time.sleep(random.uniform(8, 12))

        # 模拟向下滚动，加载更多数据
        driver.execute_script("window.scrollTo(0, 1200);")
        time.sleep(3)

        # ✨ 强力 XPath 定位器：寻找所有包含 /marketplace/item/ 链接的 a 标签的父级容器
        # 这个定位器比 data-testid 稳固得多
        cards = driver.find_elements(By.XPATH, "//a[contains(@href, '/marketplace/item/')]/ancestor::div[@role='link' or @class='x9f619']")
        
        # 如果还是找不到，尝试备用定位方案
        if not cards:
            cards = driver.find_elements(By.XPATH, "//div[@style='max-width:381px']//a/ancestor::div[1]")

        print(f"DEBUG: 页面初步定位到 {len(cards)} 个潜在商品块")

        for card in cards:
            try:
                # 提取该卡片内的所有文本
                full_text = card.text
                if not full_text or '$' not in full_text:
                    continue

                # 分割文本行
                lines = [l.strip() for l in full_text.split('\n') if l.strip()]
                
                # 通常 FB 的排列是：价格、标题、地点
                # 但有时价格前面会有“配送”等字样，我们用正则提取第一个出现的金额
                price_match = re.search(r'\$\s?([\d,.]+)', full_text)
                if not price_match:
                    continue
                current_price = float(price_match.group(1).replace(',', ''))

                # 提取标题：通常在价格这一行之后
                # 我们寻找 lines 中不包含 $ 符号且长度较长的一行作为标题
                title = "Unknown Title"
                for line in lines:
                    if '$' not in line and len(line) > 5:
                        title = line
                        break

                # 标题过滤
                title_lower = title.lower()
                if any(word in title_lower for word in ["broken", "faulty", "parts", "case", "box only"]):
                    continue

                # 提取链接：直接找该容器内或父级的 a 标签
                try:
                    link_el = card.find_element(By.TAG_NAME, "a")
                except:
                    # 如果当前 div 没 a，就找它的父级
                    link_el = card.find_element(By.XPATH, "./preceding-sibling::a | ..//a")
                
                raw_link = link_el.get_attribute("href")
                link = raw_link.split('?')[0] # 去掉追踪参数

                # 结果去重（防止同一个卡片被 ancestor 匹配多次）
                if any(item['link'] == link for item in items):
                    continue

                if min_price <= current_price <= max_price:
                    print(f"✅ FB 捕获: {title[:25]}... | ${current_price}")
                    items.append({
                        'title': title, 
                        'price': current_price, 
                        'link': link,
                        'platform': 'Facebook'
                    })

            except Exception as e:
                # print(f"DEBUG: 单个卡片解析跳过")
                continue
                
    except Exception as e:
        print(f"Facebook Scraper Error: {e}")
    finally:
        driver.quit()
        
    return items