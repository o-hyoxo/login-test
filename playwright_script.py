import asyncio
from curlwright import RequestExecutor
from playwright.async_api import TimeoutError

async def main():
    """
    使用 Curlwright 来处理 Cloudflare 验证并执行登录操作。
    """
    # 1. 初始化 Curlwright 的 RequestExecutor
    # 它将管理 Playwright 浏览器实例并自动处理 Cloudflare。
    # headless=True 使其在 GitHub Actions 等无UI环境中运行。
    executor = RequestExecutor(headless=True)
    
    # 定义一个变量以持有 Playwright 的 page 对象
    page = None

    try:
        print("使用 Curlwright 导航至登录页面并尝试绕过 Cloudflare...")
        
        # 2. 使用 Curlwright 执行一个简单的 GET 请求
        # 这个命令会导航到目标 URL，Curlwright 将在后台自动处理 Cloudflare 质询页面。
        login_url = "https://clientarea.space-hosting.net/login"
        await executor.execute(f'curl "{login_url}"')

        # 3. 从执行器中获取 page 对象
        # 当 execute 命令完成后，浏览器页面已经准备好进行后续交互了。
        page = executor.browser_manager.page
        print("Cloudflare 验证已处理，成功加载登录页面。")

        # --- 从这里开始，我们已经位于真实的登录页面，可以执行之前的操作 ---

        print("等待用户名字段出现并填写登录信息...")
        # 等待关键元素加载完成，确保页面正确
        await page.locator('input[name="username"]').wait_for(state="visible", timeout=30000)
        
        # 填写电子邮件
        await page.fill('input[name="username"]', "bryantava2@hotmail.com")
        
        # 填写密码
        await page.fill('input[name="password"]', ";Vud)pH!kXvU")
        
        print("正在处理 reCAPTCHA...")
        # reCAPTCHA 位于一个 iframe 中
        recaptcha_frame = page.frame_locator('iframe[title="reCAPTCHA"]')
        await recaptcha_frame.locator('div.recaptcha-checkbox-border').click()

        # 短暂等待 reCAPTCHA 的响应
        await page.wait_for_timeout(5000)

        print("正在点击登录按钮...")
        await page.click('button#login')

        # 验证登录是否成功，检查 URL 是否跳转
        await page.wait_for_url("**/clientarea.php**", timeout=30000)
        print("登录成功！")

    except Exception as e:
        print(f"脚本执行出错: {e}")
        # 如果 page 对象已经成功创建，就进行截图
        if page:
            screenshot_path = "error_screenshot.png"
            print(f"正在截取错误屏幕并保存至 {screenshot_path} ...")
            await page.screenshot(path=screenshot_path)
        # 重新抛出异常，以便 GitHub Action 将此步骤标记为失败
        raise

    finally:
        # 4. 确保关闭由 Curlwright 管理的浏览器
        if executor:
            await executor.close()
            print("浏览器已关闭。")

if __name__ == "__main__":
    asyncio.run(main())
