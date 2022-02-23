from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from medsenger_api import AgentApiClient, prepare_file
from selenium.webdriver.support.ui import Select
from sentry_sdk.integrations.rq import RqIntegration
from config import *
from models import *
from mail_api import get_code
import sentry_sdk


import time
import os

medsenger_client = AgentApiClient(host=MAIN_HOST, api_key=API_KEY, debug=API_DEBUG)
sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=0.0)


def create_driver(headless=HEADLESS):
    options = webdriver.ChromeOptions()
    prefs = {"download.default_directory": DOWNLOAD_PATH, 'plugins.always_open_pdf_externally': True,
             "use_system_default_printer": False, "download.prompt_for_download": False, "download_restrictions": 0,
             "profile.default_content_settings.popups": 0,
             "profile.default_content_setting_values.automatic_downloads": 1}
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    if headless:
        options.add_argument("--headless")

        if "linux" in DRIVER:
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")  # linux only
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--remote-debugging-port=9222")
            options.add_argument("--window-size=1500,1200")

    driver = webdriver.Chrome(executable_path=DRIVER, options=options)

    params = {'behavior': 'allow', 'downloadPath': DOWNLOAD_PATH}
    driver.execute_cdp_cmd('Page.setDownloadBehavior', params)

    return driver

def make_login(driver):
    try:
        driver.find_element_by_id("loginForm-email-input").send_keys(LIBRE_LOGIN)
        driver.find_element_by_id("loginForm-password-input").send_keys(LIBRE_PASS)
        driver.find_element_by_id("loginForm-submit-button").click()

        time.sleep(1)

        driver.find_element_by_id("twoFactor-step1-next-button").click()

        time.sleep(20)

        code = get_code()

        driver.find_element_by_id("twoFactor-step2-code-input").send_keys(code)
        driver.find_element_by_id("twoFactor-step2-next-button").click()
    except Exception as e:
        print("login error:", e)

    time.sleep(2)
    try:
        driver.find_element_by_id("main-header-dashboard-icon").click()
    except Exception as e:
        print("login error:", e)

    time.sleep(1)

def create_client():
    driver = create_driver()

    print("created driver...")

    driver.get("https://www.libreview.ru/")
    time.sleep(2)

    try:
        driver.find_element_by_id("submit-button").click()
        time.sleep(2)
    except:
        pass


    make_login(driver)

    return driver

def register_user(contract, client):
    contract = Contract.query.filter_by(id=contract).first()

    client.get("https://www.libreview.ru/dashboard")
    time.sleep(2)

    try:
        client.find_element_by_id("loginForm-submit-button")
        make_login(client)
    except:
        pass

    try:
        table = client.find_element_by_tag_name('tbody')

        for row in table.find_elements_by_tag_name('tr'):
            cells = row.find_elements_by_tag_name('td')
            name = cells[1].text + " " + cells[0].text
            birthday = cells[2].text
            if find_contract([contract], name, birthday):
                medsenger_client.send_message(contract.id,
                                              "Пациент найден в базе LibreView для Вашего мед. учреждения. Теперь мы сможем ежедневно автоматически присылать Вам отчеты о мониторинге. Запросить отчет в произвольное время можно в меню Действия.",
                                              only_doctor=True)
                return "exists"

        client.find_element_by_id('main-header-add-patient-button').click()

        time.sleep(1)

        surname, name, *args = contract.name.split()

        D, M, Y = contract.birthday.split('/')

        client.find_element_by_id("add-patient-firstName-field").send_keys(name)
        client.find_element_by_id("add-patient-lastName-field").send_keys(surname)

        Select(client.find_element_by_id("add-patient-dob-month-select")).select_by_value(M)

        client.find_element_by_id("add-patient-dob-day").send_keys(D)
        client.find_element_by_id("add-patient-dob-year").send_keys(Y)

        client.find_element_by_id("add-patient-email-input").send_keys(contract.email)
        Select(client.find_element_by_id("add-patient-practice-select")).select_by_visible_text(CLINIC_NAME)

        client.find_element_by_id("add-patient-modal-save-button").click()
        time.sleep(0.5)
        client.find_element_by_id("add-patient-modal-send-button").click()
        time.sleep(0.5)
    except Exception as e:
        raise e

    medsenger_client.send_message(contract.id,
                                  "Мы добавили информацию о пациенте в базу LibreView и запросили доступ к данным мониторинга. Как только пациент выдаст доступ, Вы будете автоматически получать ежедневные отчеты по мониторингу глюкозы в чат.",
                                  only_doctor=True)
    medsenger_client.send_message(contract.id,
                                  "Мы запросили доступ к данным глюкометра FreeStyle Libre. Пожалуйста, проверьте электронную почту и предоставьте доступ. После этого Ваш врач сможет автоматически получать отчеты об уровне глюкозы.",
                                  only_patient=True)

def send_reports(contracts, client):
    print("starting task...")

    try:
        contracts = Contract.query.filter(Contract.id.in_(contracts)).all()

        print("Got client")

        while True:

            client.get("https://www.libreview.ru/dashboard")
            time.sleep(3)

            try:
                client.find_element_by_id("loginForm-submit-button")
                make_login(client)
                print("relogin")
                time.sleep(1)
                client.get("https://www.libreview.ru/dashboard")
            except:
                pass
            time.sleep(1)

            continue_search = False

            table = client.find_element_by_tag_name('tbody')
            print("Got table")

            for row in table.find_elements_by_tag_name('tr'):
                cells = row.find_elements_by_tag_name('td')

                name = cells[0].text + " " + cells[1].text
                birthday = cells[2].text

                status = cells[7]
                contract = find_contract(contracts, name, birthday)

                if contract:
                    print("Found contract")

                    if status.text == "Подключено":
                        cells[0].click()

                        time.sleep(1)

                        try:
                            client.find_element_by_id("interval-select").send_keys("1\n")

                            try:
                                elm = client.find_element_by_id("pastGlucoseCard-report-button")
                            except:
                                try:
                                    elm = client.find_element_by_id("newGlucose-report-button")
                                except:
                                    elm = client.find_element_by_id("newGlucose-glucoseReports-button")

                            elm.click()
                        except Exception as e:
                            print(e)
                            medsenger_client.send_message(contract.id,
                                                          "Ошибка экспорта отчета FreeStyleLibre: недостаточно данных для создания отчета.",
                                                          only_doctor=True)
                            contracts.remove(contract)

                            continue_search = True
                            client.back()
                            break

                        time.sleep(3)

                        client.find_element_by_id("launch-reports-settings-button").click()

                        time.sleep(1)

                        checkboxes = ['20-reportSetting-toggle-checkbox', '16-reportSetting-toggle-checkbox',
                                      '5-reportSetting-toggle-checkbox',
                                      '1-reportSetting-toggle-checkbox', '8-reportSetting-toggle-checkbox',
                                      '18-reportSetting-toggle-checkbox']

                        for checkbox in checkboxes:
                            elmt = client.find_element_by_id(checkbox)

                            if elmt.get_attribute('checked'):
                                client.execute_script("arguments[0].click();", elmt)

                        checkboxes = ['10-reportSetting-toggle-checkbox', '14-reportSetting-toggle-checkbox']

                        for checkbox in checkboxes:
                            elmt = client.find_element_by_id(checkbox)

                            if not elmt.get_attribute('checked'):
                                client.execute_script("arguments[0].click();", elmt)



                        client.find_element_by_id("threshold-targetLow-input").clear()
                        for i in range(3):
                            client.find_element_by_id("threshold-targetLow-input").send_keys(
                                Keys.BACKSPACE)
                        client.find_element_by_id("threshold-targetLow-input").send_keys(
                            str(contract.yellow_bottom).replace('.', ','))
                        client.find_element_by_id("threshold-targetLow-input").send_keys(Keys.TAB)

                        actions = ActionChains(client)
                        for i in range(3):
                            actions.send_keys(Keys.BACKSPACE)
                        actions.send_keys(str(contract.yellow_top).replace('.', ','))
                        actions.send_keys(Keys.TAB)

                        for i in range(3):
                            actions.send_keys(Keys.BACKSPACE)
                        actions.send_keys(str(contract.red_bottom).replace('.', ','))
                        actions.send_keys(Keys.TAB)

                        for i in range(3):
                            actions.send_keys(Keys.BACKSPACE)
                        actions.send_keys(str(contract.red_top).replace('.', ','))
                        actions.send_keys(Keys.TAB)

                        actions.perform()

                        time.sleep(1)

                        try:
                            client.find_element_by_id("26-reportSetting-interval-select").send_keys('1\n')
                            time.sleep(0.5)
                            client.find_element_by_id("10-reportSetting-interval-select").send_keys('1\n')
                            time.sleep(0.5)
                            client.find_element_by_id("14-reportSetting-interval-select").send_keys('1\n')
                            time.sleep(0.5)
                        except:
                            pass

                        try:
                            client.find_element_by_id("save-Button").click()
                            print("clicked")
                        except:
                            pass

                        time.sleep(4)

                        client.find_element_by_id("reports-print-button").click()

                        time.sleep(10)

                        file = prepare_last_file()

                        if file:
                            print("Got report")
                            attachments = [file]
                            medsenger_client.send_message(contract.id, "Отчет FreeStyleLibre", send_from='patient',
                                                          attachments=attachments)
                        else:
                            medsenger_client.send_message(contract.id,
                                                          "Ошибка экспорта отчета FreeStyleLibre: не удалось экспортировать отчет, возможно, данных пока слишком мало.",
                                                          only_doctor=True)

                            with open('index.html', 'w') as df:
                                df.write(client.page_source)
                    else:
                        print(status, name, birthday)
                        medsenger_client.send_message(contract.id,
                                                      "Ошибка экспорта отчета FreeStyleLibre: пациент еще не открыл доступ к данным.",
                                                      only_doctor=True)

                    contracts.remove(contract)

                    continue_search = True
                    break

            if not continue_search:
                break
    except Exception as e:
        with open('index.html', 'w') as df:
            df.write(client.page_source)
        raise e

    for contract in contracts:
        medsenger_client.send_message(contract.id,
                                      "Нам не удалось найти пациента в базе LibreView. Попробуйте отключить и заного подключить интеллектуального агента, а если не поможет - можно обратиться в техническую поддержку support@medsenger.ru",
                                      only_doctor=True)


def find_contract(contracts, name, birthday):
    for contract in contracts:
        cname = contract.name.split()[1]
        csurname = contract.name.split()[0]

        print("search", name, cname, contract.birthday, birthday)

        if cname in name and csurname in name and contract.birthday == birthday:
            return contract
    return None

def prepare_last_file():
    for file in os.listdir(DOWNLOAD_PATH):
        print(file)
        if '.pdf' in file:
            prepared = prepare_file(DOWNLOAD_PATH + os.sep + file)
            os.remove(DOWNLOAD_PATH + os.sep + file)

            return prepared
    return None

if __name__ == "__main__":
    create_client()

    print("I've done")