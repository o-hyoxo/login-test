import os
import time
import sys
import subprocess
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

def get_chrome_main_version():
    """动态检测系统中安装的Chrome主版本号。"""
    try:
        output = subprocess.check_output(['google-chrome', '--version']).decode('utf-8')
        version_string = output.split(' ')[2]
        major_version = int(version_string.split('.')[0])
        print(f"成功检测到 Chrome 主版本号: {major_version}")
        return major_version
    except Exception as e:
        print(f"无法自动检测 Chrome 版本: {e}。将不指定版本号。")
        return None

def setup_driver():
    """使用深度伪装选项设置 undetected_chromedriver。"""
    print("正在设置 undetected-chromedriver...")
    options = uc.ChromeOptions()
    # 关键：尝试在无头模式下模拟一个更完整的浏览器环境
    options.add_argument("--headless=new") # 使用新的无头模式，功能更接近有头模式
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument('--window-size=1920,1080')
    # 添加常见的用户代理，避免默认的 "HeadlessChrome"
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
    
    major_version = get_chrome_main_version()
    
    # 增加补丁加载延迟，uc 官方推荐
    driver = uc.Chrome(options=options, version_main=major_version, patcher_force_close=True)
    return driver

def take_screenshot(driver, path):
    """截取当前浏览器窗口的屏幕截图。"""
    print(f"错误发生，正在截取屏幕并保存至: {path}")
    driver.save_screenshot(path)

def login():
    """执行登录网站的完整流程。"""
    driver = setup_driver()
    # 将总超时时间延长至90秒，应对更复杂的反爬虫对抗
    timeout = 90
    wait = WebDriverWait(driver, timeout)
    
    try:
        print(f"正在打开登录页面: {LOGIN_URL}")
        driver.get(LOGIN_URL)

        # 关键策略：强制等待，让所有JS加载并执行
        print("页面初步加载完成，强制等待10秒，让反爬虫脚本执行...")
        time.sleep(10)
        
        start_time = time.time()
        is_cloudflare_passed = False
        # 将轮询超时时间调整为 (总超时 - 初始等待)
        polling_timeout = timeout - 10
        print(f"启动轮询程序，在 {polling_timeout} 秒内持续检查页面状态...")
        
        while time.time() - start_time < polling_timeout:
            try:
                # 优先检查登录表单，如果存在则直接跳出
                if driver.find_element(By.ID, EMAIL_INPUT_ID).is_displayed():
                    print("检测到登录表单，Cloudflare 验证已通过或不存在。")
                    is_cloudflare_passed = True
                    break
            except:
                pass 

            try:
                # 寻找Cloudflare的Shadow DOM宿主
                shadow_host = driver.find_element(By.CSS_SELECTOR, SHADOW_DOM_HOST_SELECTOR)
                print("检测到 Cloudflare 验证，正在尝试点击...")
                
                js_script = "return arguments[0].shadowRoot.querySelector('iframe');"
                turnstile_iframe = driver.execute_script(js_script, shadow_host)
                
                driver.switch_to.frame(turnstile_iframe)
                checkbox = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, "//input[@type='checkbox']"))
                )
                # 使用JS点击，比模拟点击更稳定
                driver.execute_script("arguments[0].click();", checkbox)
                print("已点击 Cloudflare 验证框。")
                driver.switch_to.default_content()
                
                wait.until(EC.visibility_of_element_located((By.ID, EMAIL_INPUT_ID)))
                print("Cloudflare 验证成功，登录表单已加载。")
                is_cloudflare_passed = True
                break
            except:
                pass # 没找到任何元素，在下一次循环中继续尝试

            time.sleep(3) # 每次循环等待3秒

        if not is_cloudflare_passed:
            raise Exception(f"超时！在 {timeout} 秒内既未找到登录表单，也未能成功处理Cloudflare验证。")

        # --- 后续登录流程保持不变 ---
        print("开始填写登录信息...")
        # ... (后续代码与之前版本相同)
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
