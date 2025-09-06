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
EMAIL_INPUT_ID = "inputEmail"
PASSWORD_INPUT_ID = "inputPassword"
LOGIN_BUTTON_ID = "login"
RECAPTCHA_IFRAME_XPATH = "//iframe[starts-with(@name, 'a-')]"
RECAPTCHA_CHECKBOX_XPATH = '//*[@id="recaptcha-anchor"]'

def take_screenshot(driver, path):
    """截取屏幕截图。"""
    print(f"错误发生，正在截取屏幕并保存至: {path}")
    driver.save_screenshot(path)

def login():
    """使用 undetected-chromedriver 执行登录流程。"""
    driver = None
    try:
        print("正在初始化 undetected-chromedriver...")
        options = uc.ChromeOptions()
        # 在 GitHub Actions (Linux) 中，必须以无头模式运行
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # undetected-chromedriver 会自动下载并管理驱动
        driver = uc.Chrome(options=options)
        
        # 设置一个较长的全局等待时间
        wait = WebDriverWait(driver, 45)

        print(f"正在打开登录页面: {LOGIN_URL}")
        driver.get(LOGIN_URL)
        
        # --- 核心逻辑 ---
        # undetected-chromedriver 的关键优势在于它能让 Cloudflare 的挑战自动通过
        # 我们只需耐心等待登录表单元素出现即可
        print("页面加载中，等待 Cloudflare 自动验证通过...")
        print("正在等待邮箱输入框变为可见状态...")
        
        try:
            wait.until(EC.visibility_of_element_located((By.ID, EMAIL_INPUT_ID)))
            print("Cloudflare 验证通过，成功加载登录表单。")
        except TimeoutException:
            # 如果超时后仍然没有出现登录表单，说明页面卡死
            raise Exception("等待超时：Cloudflare 验证未能自动完成，无法加载登录表单。")

        # --- 登录流程 ---
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
        time.sleep(10) # 等待跳转
        
        current_url = driver.current_url
        print(f"登录后当前 URL: {current_url}")
        if "login" in current_url:
            raise Exception("登录失败，页面仍停留在登录页。")

        print("登录流程成功完成！")

    except Exception as e:
        print(f"脚本执行出错: {e}")
        if driver:
            take_screenshot(driver, SCREENSHOT_PATH)
        sys.exit(1)
    finally:
        if driver:
            print("关闭浏览器。")
            driver.quit()

if __name__ == "__main__":
    login()
