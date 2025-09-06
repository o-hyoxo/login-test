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
CLOUDFLARE_CHECKBOX_XPATH = "/html/body//div[1]/div/div[1]/div/label/input"
EMAIL_INPUT_XPATH = "/html/body/section/div/div[1]/div/form/div/div[1]/div[2]/div/input"
PASSWORD_INPUT_XPATH = "/html/body/section/div/div[1]/div/form/div/div[1]/div[3]/div[2]/input"
RECAPTCHA_IFRAME_XPATH = "//iframe[starts-with(@name, 'a-') and starts-with(@src, 'https://www.google.com/recaptcha/api2/anchor')]"
RECAPTCHA_CHECKBOX_XPATH = '//*[@id="recaptcha-anchor"]'
LOGIN_BUTTON_XPATH = "/html/body/section/div/div[1]/div/form/div/div[1]/div[5]/button"

def setup_driver():
    """在 GitHub Actions 环境中设置 Chrome WebDriver。"""
    options = webdriver.ChromeOptions()
    # 在无头模式下运行，这对于 CI/CD 环境至关重要
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080") # 设置窗口大小以确保元素可见
    
    # 使用 webdriver_manager 自动管理驱动程序
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
    except ImportError:
        # 如果 webdriver_manager 不可用，则假定 chromedriver 在 PATH 中
        service = Service()
        
    return webdriver.Chrome(service=service, options=options)

def take_screenshot(driver, path):
    """截取当前浏览器窗口的屏幕截图。"""
    print(f"错误发生，正在截取屏幕并保存至: {path}")
    driver.save_screenshot(path)

def login():
    """执行登录网站的完整流程。"""
    driver = setup_driver()
    wait = WebDriverWait(driver, 20) # 增加等待时间以应对网络延迟

    try:
        print(f"正在打开登录页面: {LOGIN_URL}")
        driver.get(LOGIN_URL)

        # 步骤 1: 处理 Cloudflare 验证 (如果出现)
        try:
            print("正在检查 Cloudflare 验证...")
            cloudflare_checkbox = wait.until(
                EC.presence_of_element_located((By.XPATH, CLOUDFLARE_CHECKBOX_XPATH))
            )
            print("检测到 Cloudflare 验证，正在尝试点击...")
            # 使用 JavaScript 点击以避免被遮挡
            driver.execute_script("arguments[0].click();", cloudflare_checkbox)
            print("已点击 Cloudflare 验证框，等待页面跳转...")
            # 等待 URL 变化或登录表单出现
            wait.until(EC.presence_of_element_located((By.XPATH, EMAIL_INPUT_XPATH)))
        except TimeoutException:
            print("未找到 Cloudflare 验证，或页面已通过，继续执行。")

        # 步骤 2: 填写账户和密码
        print("正在定位邮箱输入框...")
        email_input = wait.until(EC.visibility_of_element_located((By.XPATH, EMAIL_INPUT_XPATH)))
        print("正在填写邮箱...")
        email_input.send_keys(EMAIL)

        print("正在定位密码输入框...")
        password_input = wait.until(EC.visibility_of_element_located((By.XPATH, PASSWORD_INPUT_XPATH)))
        print("正在填写密码...")
        password_input.send_keys(PASSWORD)
        time.sleep(1) # 短暂等待，模拟真人输入

        # 步骤 3: 点击 reCAPTCHA
        # 注意: 自动点击 reCAPTCHA 可能会触发更复杂的图片验证，这超出了 Selenium 的能力范围。
        # 此脚本只能完成点击操作。如果出现图片验证，脚本将失败。
        print("正在定位 reCAPTCHA iframe...")
        recaptcha_iframe = wait.until(EC.presence_of_element_located((By.XPATH, RECAPTCHA_IFRAME_XPATH)))
        driver.switch_to.frame(recaptcha_iframe)
        
        print("正在点击 reCAPTCHA 复选框...")
        recaptcha_checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, RECAPTCHA_CHECKBOX_XPATH)))
        recaptcha_checkbox.click()
        
        # 切换回主页面
        driver.switch_to.default_content()
        print("已点击 reCAPTCHA，等待验证结果...")
        time.sleep(5) # 等待几秒钟，让 reCAPTCHA 完成验证

        # 步骤 4: 点击登录按钮
        print("正在点击登录按钮...")
        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, LOGIN_BUTTON_XPATH)))
        login_button.click()
        
        # 验证是否登录成功 (例如，检查 URL 是否跳转或页面上是否出现特定元素)
        # 这里我们简单地等待10秒，然后检查URL
        time.sleep(10)
        if "login" in driver.current_url:
            raise Exception("登录失败，页面仍停留在登录页。")

        print("登录流程成功完成！")

    except Exception as e:
        print(f"脚本执行出错: {e}")
        take_screenshot(driver, SCREENSHOT_PATH)
        # 退出并返回非零状态码，以使 GitHub Action 标记为失败
        sys.exit(1)
    finally:
        print("关闭浏览器。")
        driver.quit()

if __name__ == "__main__":
    login()
