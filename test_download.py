from selenium import webdriver
import time

def enable_download_headless(browser,download_dir):
    browser.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
    params = {'cmd':'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
    browser.execute("send_command", params)

if __name__ == '__main__':
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument('--no-sandbox')
    options.add_argument('--verbose')
    options.add_experimental_option("prefs", {
        "download.default_directory": "/var/www/libre-medsenger-bot/downloads/",
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing_for_trusted_sources_enabled": False,
        "safebrowsing.enabled": False
    })
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--headless')
    driver_path = "/var/www/libre-medsenger-bot/drivers/chromedriver_linux"
    driver = webdriver.Chrome(driver_path, options=options)
    print("Created driver")
    enable_download_headless(driver, "/var/www/libre-medsenger-bot/downloads/")
    print("Enabled")
    driver.get("https://medsenger.ru/medsenger.pdf")

    time.sleep(3)

    driver.close()