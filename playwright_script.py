import asyncio
from playwright.async_api import async_playwright, TimeoutError

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            print("正在导航至登录页面...")
            await page.goto("https://clientarea.space-hosting.net/login", timeout=60000, wait_until="domcontentloaded")

            # --- 优化后的Cloudflare验证处理逻辑 ---
            try:
                print("正在检查Cloudflare验证...")
                # Cloudflare验证内容通常在一个特定的iframe中，我们首先定位这个iframe
                # 使用包含'challenges.cloudflare.com'的src属性来定位，这比XPath更可靠
                challenge_frame_locator = page.frame_locator('iframe[src*="challenges.cloudflare.com"]')
                
                # 等待并点击iframe中的复选框
                checkbox = challenge_frame_locator.locator('label.ctp-checkbox-label input[type="checkbox"]')
                await checkbox.wait_for(state="visible", timeout=20000) # 增加等待时间
                
                print("检测到Cloudflare验证，正在点击...")
                await checkbox.click()

                # 关键步骤：点击验证后，等待登录页面的关键元素（如用户名字段）出现，确认已跳转成功
                print("Cloudflare验证已点击，等待登录页面加载...")
                await page.locator('input[name="username"]').wait_for(state="visible", timeout=30000)
                print("登录页面已成功加载。")

            except TimeoutError:
                # 如果在20秒内没有找到Cloudflare验证框，就假定页面已是登录页，直接继续
                print("未检测到Cloudflare验证，或已直接加载登录页，继续执行。")
            
            print("正在填写登录信息...")
            # 填写电子邮件
            await page.fill('input[name="username"]', "bryantava2@hotmail.com")
            
            # 填写密码
            await page.fill('input[name="password"]', ";Vud)pH!kXvU")
            
            print("正在处理reCAPTCHA...")
            # reCAPTCHA同样在iframe中
            recaptcha_frame = page.frame_locator('iframe[title="reCAPTCHA"]')
            await recaptcha_frame.locator('div.recaptcha-checkbox-border').click()

            # 等待reCAPTCHA处理
            await page.wait_for_timeout(5000)

            print("正在点击登录按钮...")
            await page.click('button#login')

            # 验证登录是否成功，例如检查URL是否跳转到了客户区
            await page.wait_for_url("**/clientarea.php**", timeout=30000)
            print("登录成功！")

        except Exception as e:
            print(f"脚本执行出错: {e}")
            screenshot_path = "error_screenshot.png"
            print(f"正在截取错误屏幕并保存至 {screenshot_path} ...")
            await page.screenshot(path=screenshot_path)
            # 重新抛出异常以使GitHub Action步骤失败
            raise

        finally:
            await browser.close()
            print("浏览器已关闭。")

if __name__ == "__main__":
    asyncio.run(main())
