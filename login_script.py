import os
import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# --- 配置 ---
LOGIN_URL = "https://clientarea.space-hosting.net/login"
EMAIL = "bryantava2@hotmail.com"
PASSWORD = ";Vud)pH!kXvU"
SCREENSHOT_PATH = "error_screenshot.png"

# --- XPaths ---
# !! 更新: Cloudflare Turnstile 验证是在一个 iframe 中
CLOUDFLARE_TURNSTILE_IFRAME_XPATH = "//iframe[starts-with(@src, 'https://challenges.cloudflare.com')]"
CLOUDFLARE_INTERNAL_CHECKBOX_XPATH = "//input[@type='checkbox']"

# 登录表单元素
EMAIL_INPUT_XPATH = "/html/body/section/div/div[1]/div/form/div/div[1]/div[2]/div/input"
PASSWORD_INPUT_XPATH = "/html/body/section/div/div[1]/div/form/div/div[1]/div[3]/div[2]/input"
RECAPTCHA_IFRAME_XPATH = "//iframe[starts-with(@name, 'a-') and starts-with(@src, 'https://www.google.com/recaptcha/api2/anchor')]"
RECAPTCHA_CHECKBOX_XPATH = '//*[@id="recaptcha-anchor"]'
LOGIN_BUTTON_XPATH = "/html/body/section/div/div[1]/div/form/div/div[1]/div[5]/button"

def setup_driver():
    """在 GitHub Actions 环境中设置 Chrome WebDriver。"""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
    except ImportError:
        service = Service()
        
    return webdriver.Chrome(service=service, options=options)

def take_screenshot(driver, path):
    """截取当前浏览器窗口的屏幕截图。"""
    print(f"错误发生，正在截取屏幕并保存至: {path}")
    driver.save_screenshot(path)

def login():
    """执行登录网站的完整流程。"""
    driver = setup_driver()
    # 增加等待时间以应对 Cloudflare 和 reCAPTCHA 的加载
    wait = WebDriverWait(driver, 30)

    try:
        print(f"正在打开登录页面: {LOGIN_URL}")
        driver.get(LOGIN_URL)

        # 步骤 1: 处理 Cloudflare Turnstile 验证 (如果出现)
        try:
            print("正在检查 Cloudflare Turnstile 验证...")
            
            # 等待 Cloudflare iframe 加载完成
            turnstile_iframe = wait.until(
                EC.presence_of_element_located((By.XPATH, CLOUDFLARE_TURNSTILE_IFRAME_XPATH))
            )
            
            print("检测到 Cloudflare iframe，正在切换进入...")
            driver.switch_to.frame(turnstile_iframe)
            
            # 等待并点击 iframe 内部的验证框
            turnstile_checkbox = wait.until(
                EC.element_to_be_clickable((By.XPATH, CLOUDFLARE_INTERNAL_CHECKBOX_XPATH))
            )
            print("正在点击 Cloudflare 验证框...")
            turnstile_checkbox.click()
            
            print("已点击验证框。切换回主页面并等待登录表单加载...")
            driver.switch_to.default_content()
            
            # 关键步骤: 等待 Cloudflare 验证通过后，登录表单完全可见
            wait.until(EC.visibility_of_element_located((By.XPATH, EMAIL_INPUT_XPATH)))
            print("Cloudflare 验证通过，登录页面已加载。")

        except TimeoutException:
            print("未找到 Cloudflare 验证，或页面已直接加载。继续执行。")

        # 步骤 2: 填写账户和密码
        print("正在定位邮箱输入框...")
        email_input = wait.until(EC.visibility_of_element_located((By.XPATH, EMAIL_INPUT_XPATH)))
        print("正在填写邮箱...")
        email_input.send_keys(EMAIL)

        print("正在定位密码输入框...")
        password_input = wait.until(EC.visibility_of_element_located((By.XPATH, PASSWORD_INPUT_XPATH)))
        print("正在填写密码...")
        password_input.send_keys(PASSWORD)
        time.sleep(1)

        # 步骤 3: 点击 reCAPTCHA
        print("正在定位 reCAPTCHA iframe...")
        recaptcha_iframe = wait.until(EC.presence_of_element_located((By.XPATH, RECAPTCHA_IFRAME_XPATH)))
        driver.switch_to.frame(recaptcha_iframe)
        
        print("正在点击 reCAPTCHA 复选框...")
        recaptcha_checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, RECAPTCHA_CHECKBOX_XPATH)))
        recaptcha_checkbox.click()
        
        driver.switch_to.default_content()
        print("已点击 reCAPTCHA，等待验证结果...")
        time.sleep(5)

        # 步骤 4: 点击登录按钮
        print("正在点击登录按钮...")
        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, LOGIN_BUTTON_XPATH)))
        # 使用 JavaScript 点击以防按钮被遮挡
        driver.execute_script("arguments[0].click();", login_button)
        
        print("已点击登录，等待页面跳转...")
        time.sleep(10) # 等待足够长的时间以确认登录结果
        
        # 验证是否登录成功
        current_url = driver.current_url
        print(f"登录后当前 URL: {current_url}")
        if "login" in current_url:
            raise Exception("登录失败，页面仍停留在登录页。")

        print("登录流程成功完成！")

    except Exception as e:
        print(f"脚本执行出错: {e}")
        take_screenshot(driver, SCREENSHOT_PATH)
        sys.exit(1) # 退出并返回错误码，使 Action 失败
    finally:
        print("关闭浏览器。")
        driver.quit()

if __name__ == "__main__":
    login()
