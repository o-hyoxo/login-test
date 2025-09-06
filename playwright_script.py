import asyncio
from playwright.async_api import async_playwright, TimeoutError

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # 在无头模式下运行
        page = await browser.new_page()

        try:
            print("正在导航至登录页面...")
            await page.goto("https://clientarea.space-hosting.net/login", timeout=60000)

            # 尝试处理Cloudflare验证
            try:
                print("正在检查Cloudflare验证...")
                cloudflare_checkbox = page.locator('//div[1]/div/div[1]/div/label/input').first
                await cloudflare_checkbox.wait_for(state="visible", timeout=10000)
                print("检测到Cloudflare验证，正在点击...")
                await cloudflare_checkbox.click()
                print("已点击Cloudflare验证框。")
                # 等待页面导航或内容加载
                await page.wait_for_load_state('networkidle', timeout=30000)
            except TimeoutError:
                print("未检测到Cloudflare验证，继续执行。")

            print("正在填写登录信息...")
            # 填写电子邮件
            await page.fill('input[name="username"]', "bryantava2@hotmail.com")
            
            # 填写密码
            await page.fill('input[name="password"]', ";Vud)pH!kXvU")
            
            print("正在处理reCAPTCHA...")
            # 点击reCAPTCHA复选框
            recaptcha_frame = page.frame_locator('iframe[title="reCAPTCHA"]')
            await recaptcha_frame.locator('div.recaptcha-checkbox-border').click()

            # 等待reCAPTCHA验证完成（这里使用一个延时来等待，实际情况可能需要更复杂的处理）
            await page.wait_for_timeout(5000) 

            print("正在点击登录按钮...")
            # 点击登录按钮
            await page.click('button#login')

            # 验证登录是否成功，例如检查URL或页面上的某个元素
            await page.wait_for_url("**/clientarea.php**", timeout=30000)
            print("登录成功！")

        except Exception as e:
            print(f"脚本执行出错: {e}")
            # 创建一个在GitHub Actions中有效的文件路径
            screenshot_path = "error_screenshot.png"
            print(f"正在截取错误屏幕并保存至 {screenshot_path} ...")
            await page.screenshot(path=screenshot_path)
            # 抛出异常以使GitHub Action步骤失败
            raise

        finally:
            await browser.close()
            print("浏览器已关闭。")

if __name__ == "__main__":
    asyncio.run(main())
