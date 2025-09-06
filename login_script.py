import os
import sys
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# --- 配置 ---
LOGIN_URL = "https://clientarea.space-hosting.net/login"
EMAIL = "bryantava2@hotmail.com"
PASSWORD = ";Vud)pH!kXvU"
SCREENSHOT_PATH = "error_screenshot.png"

# --- 定位器 (Playwright Selectors) ---
CLOUDFLARE_IFRAME_SELECTOR = "iframe[src*='challenges.cloudflare.com']"
CLOUDFLARE_CHECKBOX_SELECTOR = "input[type='checkbox']"
EMAIL_INPUT_SELECTOR = "#inputEmail"
PASSWORD_INPUT_SELECTOR = "#inputPassword"
LOGIN_BUTTON_SELECTOR = "#login"
RECAPTCHA_IFRAME_SELECTOR = "iframe[src*='google.com/recaptcha']"
RECAPTCHA_CHECKBOX_SELECTOR = "#recaptcha-anchor"

def login():
    """使用 Playwright 执行登录流程。"""
    with sync_playwright() as p:
        # 启动一个经过伪装的 Chromium 浏览器
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        # 创建一个带有伪装用户代理的上下文
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print(f"正在打开登录页面: {LOGIN_URL}")
            page.goto(LOGIN_URL, timeout=60000, wait_until="domcontentloaded")

            print("页面初步加载完成，等待15秒，让所有反爬虫脚本执行...")
            time.sleep(15)

            # --- 智能判断和处理Cloudflare ---
            # Playwright 可以直接定位到 iframe 内部的元素
            cloudflare_iframe = page.frame_locator(CLOUDFLARE_IFRAME_SELECTOR)
            
            try:
                print("正在检查 Cloudflare 验证...")
                # 等待 iframe 内的复选框出现，最多等待30秒
                cloudflare_checkbox = cloudflare_iframe.locator(CLOUDFLARE_CHECKBOX_SELECTOR)
                cloudflare_checkbox.wait_for(state="visible", timeout=30000)
                
                print("检测到 Cloudflare 验证框，正在尝试点击...")
                cloudflare_checkbox.click()
                print("已点击 Cloudflare 验证框。")

                # 等待登录表单出现作为验证成功的标志
                print("等待登录表单加载...")
                page.locator(EMAIL_INPUT_SELECTOR).wait_for(state="visible", timeout=30000)
                print("Cloudflare 验证成功，登录表单已加载。")

            except PlaywrightTimeoutError:
                print("未在30秒内找到 Cloudflare 验证框，或验证已自动通过。")
                # 确认登录表单是否已存在，如果不存在则失败
                try:
                    page.locator(EMAIL_INPUT_SELECTOR).wait_for(state="visible", timeout=5000)
                    print("确认登录表单已可见。")
                except PlaywrightTimeoutError:
                    raise Exception("超时！页面既未显示 Cloudflare 验证框，也未加载登录表单。")

            # --- 登录流程 ---
            print("开始填写登录信息...")
            page.fill(EMAIL_INPUT_SELECTOR, EMAIL)
            page.fill(PASSWORD_INPUT_SELECTOR, PASSWORD)
            print("账户和密码已填写。")
            
            print("正在处理 reCAPTCHA...")
            recaptcha_iframe = page.frame_locator(RECAPTCHA_IFRAME_SELECTOR)
            recaptcha_checkbox = recaptcha_iframe.locator(RECAPTCHA_CHECKBOX_SELECTOR)
            recaptcha_checkbox.click()
            print("已点击 reCAPTCHA。")

            # 等待几秒让 reCAPTCHA 可能的验证完成
            time.sleep(5)

            print("正在点击登录按钮...")
            page.click(LOGIN_BUTTON_SELECTOR)

            print("已点击登录，等待页面跳转确认...")
            # 等待URL不再包含 "login"，最多等待15秒
            page.wait_for_url(lambda url: "login" not in url, timeout=15000)
            
            print(f"登录成功！当前 URL: {page.url}")

        except Exception as e:
            print(f"脚本执行出错: {e}")
            print("正在截取屏幕...")
            page.screenshot(path=SCREENSHOT_PATH, full_page=True)
            sys.exit(1)
        finally:
            print("关闭浏览器。")
            browser.close()

if __name__ == "__main__":
    login()
