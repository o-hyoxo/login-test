import os
import time
import sys
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# --- 配置 ---
LOGIN_URL = "https://clientarea.space-hosting.net/login"
EMAIL = "bryantava2@hotmail.com"
PASSWORD = ";Vud)pH!kXvU"
SCREENSHOT_PATH = "error_screenshot.png"

# --- 定位器 ---
SHADOW_DOM_HOST_SELECTOR = "div#turnstile-wrapper"
EMAIL_INPUT_ID = "inputEmail"
PASSWORD_INPUT_ID = "inputPassword"
LOGIN_BUTTON_ID = "login"
RECAPTCHA_IFRAME_XPATH = "//iframe[starts-with(@name, 'a-')]"
RECAPTCHA_CHECKBOX_XPATH = '//*[@id="recaptcha-anchor"]'

def setup_driver():
    """使用 undetected_chromedriver 设置驱动程序。"""
    print("正在设置 undetected-chromedriver...")
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument('--window-size=1920,1080')
    
    # 关键修改：移除 version_main 参数，让库自动检测已安装的 Chrome 版本
    # 这大大增强了脚本在不同环境下的兼容性
    print("自动检测已安装的Chrome版本...")
    driver = uc.Chrome(options=options) 
    return driver

def take_screenshot(driver, path):
    """截取当前浏览器窗口的屏幕截图。"""
    print(f"错误发生，正在截取屏幕并保存至: {path}")
    driver.save_screenshot(path)

def login():
    """执行登录网站的完整流程。"""
    driver = setup_driver()
    timeout = 60
    wait = WebDriverWait(driver, timeout)
    
    try:
        print(f"正在打开登录页面: {LOGIN_URL}")
        driver.get(LOGIN_URL)

        start_time = time.time()
        is_cloudflare_passed = False
        print("启动轮询程序，在60秒内持续检查页面状态...")
        
        while time.time() - start_time < timeout:
            try:
                driver.find_element(By.ID, EMAIL_INPUT_ID)
                print("检测到登录表单，Cloudflare 验证已通过或不存在。")
                is_cloudflare_passed = True
                break
            except:
                pass 

            try:
                shadow_host = driver.find_element(By.CSS_SELECTOR, SHADOW_DOM_HOST_SELECTOR)
                print("检测到 Cloudflare 验证，正在尝试点击...")
                
                js_script = "return arguments[0].shadowRoot.querySelector('iframe');"
                turnstile_iframe = driver.execute_script(js_script, shadow_host)
                
                driver.switch_to.frame(turnstile_iframe)
                checkbox = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//input[@type='checkbox']"))
                )
                checkbox.click()
                print("已点击 Cloudflare 验证框。")
                driver.switch_to.default_content()
                
                wait.until(EC.visibility_of_element_located((By.ID, EMAIL_INPUT_ID)))
                print("Cloudflare 验证成功，登录表单已加载。")
                is_cloudflare_passed = True
                break
            except:
                pass 

            time.sleep(2)

        if not is_cloudflare_passed:
            raise Exception("超时！在60秒内既未找到登录表单，也未能成功处理Cloudflare验证。")

        print("开始填写登录信息...")
        driver.find_element(By.ID, EMAIL_INPUT_ID).send_keys(EMAIL)
        driver.find_element(By.ID, PASSWORD_INPUT_ID).send_keys(PASSWORD)
        print("账户和密码已填写。")
        time.sleep(1)

        print("正在处理 reCAPTCHA...")
        recaptcha_iframe = wait.until(EC.presence_of_element_located((By.XPATH, RECAPTCHA_IFRAME_XPATH)))
        driver.switch_to.frame(recaptcha_iframe)
        
        wait.until(EC.element_to_be_clickable((By.XPATH, RECAPTCHA_CHECKBOX_XPATH))).click()
        
        driver.switch_to.default_content()
        print("已点击 reCAPTCHA，等待验证...")
        time.sleep(5)

        print("正在点击登录按钮...")
        driver.find_element(By.ID, LOGIN_BUTTON_ID).click()
        
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
