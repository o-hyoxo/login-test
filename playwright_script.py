import asyncio
from curlwright.core.request_executor import RequestExecutor
from playwright.async_api import TimeoutError

async def main():
    """
    使用 Curlwright 来处理 Cloudflare 验证并执行登录操作。
    """
    executor = RequestExecutor(headless=True)
    page = None

    try:
        print("使用 Curlwright 导航至登录页面并尝试绕过 Cloudflare...")
        login_url = "https://clientarea.space-hosting.net/login"
        await executor.execute(f'curl "{login_url}"')
        
        page = executor.browser_manager.page
        print("Cloudflare 验证已处理，成功加载登录页面。")

        print("等待用户名字段出现并填写登录信息...")
        await page.locator('input[name="username"]').wait_for(state="visible", timeout=30000)
        
        await page.fill('input[name="username"]', "bryantava2@hotmail.com")
        await page.fill('input[name="password"]', ";Vud)pH!kXvU")
        
        print("正在处理 reCAPTCHA...")
        recaptcha_frame = page.frame_locator('iframe[title="reCAPTCHA"]')
        await recaptcha_frame.locator('div.recaptcha-checkbox-border').click()

        await page.wait_for_timeout(5000)

        print("正在点击登录按钮...")
        await page.click('button#login')

        await page.wait_for_url("**/clientarea.php**", timeout=30000)
        print("登录成功！")

    except Exception as e:
        print(f"脚本执行出错: {e}")
        if page:
            screenshot_path = "error_screenshot.png"
            print(f"正在截取错误屏幕并保存至 {screenshot_path} ...")
            await page.screenshot(path=screenshot_path)
        raise

    finally:
        if executor:
            await executor.close()
            print("浏览器已关闭。")

if __name__ == "__main__":
    asyncio.run(main())
