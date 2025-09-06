import asyncio
from playwright.async_api import async_playwright, TimeoutError

async def main():
    async with async_playwright() as p:
        # 启动浏览器，添加--no-sandbox参数以增强在GitHub Actions等容器环境中的兼容性
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        # 创建一个带有真实浏览器User-Agent的上下文，降低被识别为机器人的概率
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            print("1. 正在导航至登录页面...")
            # 使用 'domcontentloaded' 可以更快地开始页面交互
            await page.goto("https://clientarea.space-hosting.net/login", timeout=60000, wait_until="domcontentloaded")

            # --- 参考 DrissionPage 逻辑优化 Cloudflare 验证处理 ---
            print("2. 正在检查 Cloudflare 人机验证...")
            try:
                # 等待Cloudflare的iframe出现。这是最关键和最可靠的一步，类似DrissionPage中的iframe查找逻辑。
                challenge_frame_locator = page.frame_locator('iframe[src*="challenges.cloudflare.com"]')
                
                # 在iframe内部，定位并点击复选框。
                checkbox = challenge_frame_locator.locator('input[type="checkbox"]')
                await checkbox.wait_for(state="visible", timeout=20000) # 等待复选框可见
                
                print("   检测到Cloudflare验证，正在点击...")
                await checkbox.click()

                # 关键步骤：确认验证成功。我们不等待元素消失，而是等待下一个页面的关键元素（用户名字段）出现。
                # 这是一种更可靠的确认方式，确保我们成功进入了登录页。
                print("   Cloudflare验证已点击，等待登录页面加载...")
                await page.locator('input[name="username"]').wait_for(state="visible", timeout=30000)
                print("   Cloudflare验证通过，登录页面已成功加载。")

            except TimeoutError:
                # 如果在指定时间内没有找到Cloudflare验证框，脚本会假定页面已是登录页。
                print("   未检测到Cloudflare验证，或已直接进入登录页，继续执行。")
            
            print("3. 正在填写登录信息...")
            await page.fill('input[name="username"]', "bryantava2@hotmail.com")
            await page.fill('input[name="password"]', ";Vud)pH!kXvU")
            
            print("4. 正在处理 reCAPTCHA 验证...")
            # reCAPTCHA同样在iframe中
            recaptcha_frame = page.frame_locator('iframe[title="reCAPTCHA"]')
            await recaptcha_frame.locator('div.recaptcha-checkbox-border').click()

            # 等待reCAPTCHA处理（自动化脚本通常无法完全通过reCAPTCHA，但点击是必须的步骤）
            await page.wait_for_timeout(3000)

            print("5. 正在点击登录按钮...")
            await page.click('button#login')

            # 6. 验证登录是否成功
            print("6. 正在验证登录结果...")
            await page.wait_for_url("**/clientarea.php**", timeout=30000)
            print("\n登录成功！脚本执行完毕。")

        except Exception as e:
            print(f"\n脚本执行出错: {e}")
            screenshot_path = "error_screenshot.png"
            print(f"正在截取错误屏幕并保存至 {screenshot_path} ...")
            await page.screenshot(path=screenshot_path)
            # 重新抛出异常，这对于让GitHub Action识别到失败并执行后续步骤（如上传截图）至关重要
            raise

        finally:
            await browser.close()
            print("浏览器已关闭。")

if __name__ == "__main__":
    asyncio.run(main())
