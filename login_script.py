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
CLOUDFLARE_TURNSTILE_IFRAME_XPATH = "//iframe[starts-with(@src, 'https://challenges.cloudflare.com')]"
CLOUDFLARE_INTERNAL_CHECKBOX_XPATH = "//input[@type='checkbox']"

EMAIL_INPUT_XPATH = "//*[@id='inputEmail']"  # 使用 ID 定位器，更稳定
PASSWORD_INPUT_XPATH = "//*[@id='inputPassword']" # 使用 ID 定位器，更稳定
RECAPTCHA_IFRAME_XPATH = "//iframe[starts-with(@name, 'a-') and starts-with(@src, 'https://www.google.com/recaptcha/api2/anchor')]"
RECAPTCHA_CHECKBOX_XPATH = '//*[@id="recaptcha-anchor"]'
LOGIN_BUTTON_XPATH = "//*[@id='login']" # 使用 ID 定位器，更稳定

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
    # 增加总等待时间以应对不稳定的网络环境
    wait = WebDriverWait(driver, 40)

    try:
        print(f"正在打开登录页面: {LOGIN_URL}")
        driver.get(LOGIN_URL)
        
        # --- 重构后的智能验证逻辑 ---
        print("正在检查页面状态：判断是Cloudflare验证还是登录表单...")
        try:
            # 1. 首先在15秒内尝试寻找Cloudflare iframe
            short_wait = WebDriverWait(driver, 15)
            turnstile_iframe = short_wait.until(
                EC.presence_of_element_located((By.XPATH, CLOUDFLARE_TURNSTILE_IFRAME_XPATH))
            )
            
            # 2. 如果找到了，则执行Cloudflare验证流程
            print("检测到Cloudflare验证，正在处理...")
            driver.switch_to.frame(turnstile_iframe)
            
            turnstile_checkbox = wait.until(
                EC.element_to_be_clickable((By.XPATH, CLOUDFLARE_INTERNAL_CHECKBOX_XPATH))
            )
            turnstile_checkbox.click()
            print("已点击Cloudflare验证框。")
            
            driver.switch_to.default_content()
            
            # 3. 验证后，必须等待登录表单加载完成
            print("等待登录表单加载...")
            wait.until(EC.visibility_of_element_located((By.XPATH, EMAIL_INPUT_XPATH)))
            print("Cloudflare验证通过，登录表单已可见。")

        except TimeoutException:
            # 4. 如果15秒内没找到Cloudflare iframe，则必须确认登录表单已存在
            print("未检测到Cloudflare iframe，正在确认登录表单是否已加载...")
            try:
                wait.until(EC.visibility_of_element_located((By.XPATH, EMAIL_INPUT_XPATH)))
                print("确认登录表单已直接可见，跳过Cloudflare处理步骤。")
            except TimeoutException:
                # 5. 如果既没找到Cloudflare也没找到登录表单，则页面卡住，抛出错误
                raise Exception("页面加载失败：既未找到Cloudflare验证也未找到登录表单。")

        # --- 登录流程 ---
        # 此时可以确保登录表单是可见的
        print("开始填写登录信息...")
        email_input = driver.find_element(By.XPATH, EMAIL_INPUT_XPATH)
        email_input.send_keys(EMAIL)
        
        password_input = driver.find_element(By.XPATH, PASSWORD_INPUT_XPATH)
        password_input.send_keys(PASSWORD)
        print("账户和密码已填写。")
        time.sleep(1)

        print("正在处理 reCAPTCHA...")
        recaptcha_iframe = wait.until(EC.presence_of_element_located((By.XPATH, RECAPTCHA_IFRAME_XPATH)))
        driver.switch_to.frame(recaptcha_iframe)
        
        recaptcha_checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, RECAPTCHA_CHECKBOX_XPATH)))
        recaptcha_checkbox.click()
        
        driver.switch_to.default_content()
        print("已点击 reCAPTCHA，等待验证...")
        time.sleep(5)

        print("正在点击登录按钮...")
        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, LOGIN_BUTTON_XPATH)))
        driver.execute_script("arguments[0].click();", login_button)
        
        print("已点击登录，等待页面跳转确认...")
        time.sleep(10)
        
        current_url = driver.current_url
        print(f"登录后当前 URL: {current_url}")
        if "login" in current_url:
            raise Exception("登录失败，页面仍停留在登录页。")

        print("登录流程成功完成！")

    except Exception as e:
        print(f"脚本执行出错: {e}")
        take_screenshot(driver, SCREENSHOT_PATH)
        sys.exit(1)
    finally:
        print("关闭浏览器。")
        driver.quit()

if __name__ == "__main__":
    login()
