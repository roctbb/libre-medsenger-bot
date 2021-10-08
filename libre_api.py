from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from medsenger_api import AgentApiClient, prepare_file
from selenium.webdriver.support.ui import Select
from config import *
import time
import os

medsenger_client = AgentApiClient(host=MAIN_HOST, api_key=API_KEY, debug=API_DEBUG)

def create_driver(headless=HEADLESS):
    options = webdriver.ChromeOptions()
    prefs = {"download.default_directory": DOWNLOAD_PATH}
    options.add_experimental_option("prefs", prefs)

    if headless:
        options.add_argument("--headless")

        if "linux" in DRIVER:
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")  # linux only

    return webdriver.Chrome(executable_path=DRIVER, options=options)

def create_client(headless=HEADLESS):
    driver = create_driver(headless)

    driver.get("https://www.libreview.ru/")
    time.sleep(2)

    driver.find_element_by_id("submit-button").click()

    time.sleep(2)

    driver.find_element_by_id("loginForm-email-input").send_keys(LIBRE_LOGIN)
    driver.find_element_by_id("loginForm-password-input").send_keys(LIBRE_PASS)
    driver.find_element_by_id("loginForm-submit-button").click()

    time.sleep(1)

    driver.find_element_by_id("main-header-dashboard-icon").click()

    time.sleep(1)

    return driver

def register_user(contract):
    driver = create_client()
    table = driver.find_element_by_tag_name('tbody')

    for row in table.find_elements_by_tag_name('tr'):
        cells = row.find_elements_by_tag_name('td')
        name = cells[1].text + " " + cells[0].text
        birthday = cells[2].text
        if find_contract([contract], name, birthday):
            return "exists"

    driver.find_element_by_id('main-header-add-patient-button').click()

    time.sleep(1)

    surname, name, *args = contract.name.split()

    D, M, Y = contract.birthday.split('/')

    driver.find_element_by_id("add-patient-firstName-field").send_keys(name)
    driver.find_element_by_id("add-patient-lastName-field").send_keys(surname)

    Select(driver.find_element_by_id("add-patient-dob-month-select")).select_by_value(M)

    driver.find_element_by_id("add-patient-dob-day").send_keys(D)
    driver.find_element_by_id("add-patient-dob-year").send_keys(Y)

    driver.find_element_by_id("add-patient-email-input").send_keys(contract.email)
    Select(driver.find_element_by_id("add-patient-practice-select")).select_by_visible_text(CLINIC_NAME)

    driver.find_element_by_id("add-patient-modal-save-button").click()
    time.sleep(0.5)
    driver.find_element_by_id("add-patient-modal-send-button").click()
    time.sleep(0.5)
    driver.close()

    return "added"

def send_reports(contracts):
    driver = create_client()

    print("Got client")

    table = driver.find_element_by_tag_name('tbody')
    print("Got table")

    for row in table.find_elements_by_tag_name('tr'):
        cells = row.find_elements_by_tag_name('td')

        name = cells[1].text + " " + cells[0].text
        birthday = cells[2].text

        status = cells[7]
        contract = find_contract(contracts, name, birthday)

        print("Found contract")

        if contract:
            if status.text == "Подключено":
                cells[0].click()

                time.sleep(1)

                driver.find_element_by_id("interval-select").send_keys("1\n")
                driver.find_element_by_id("pastGlucoseCard-report-button").click()

                time.sleep(3)

                driver.find_element_by_id("launch-reports-settings-button").click()

                time.sleep(1)

                checkboxes = ['20-reportSetting-toggle-checkbox', '16-reportSetting-toggle-checkbox', '5-reportSetting-toggle-checkbox',
                              '1-reportSetting-toggle-checkbox', '8-reportSetting-toggle-checkbox', '10-reportSetting-toggle-checkbox',
                              '18-reportSetting-toggle-checkbox', '14-reportSetting-toggle-checkbox']

                for checkbox in checkboxes:
                    elmt = driver.find_element_by_id(checkbox)

                    if elmt.get_attribute('checked'):
                        driver.execute_script("arguments[0].click();", elmt)

                driver.find_element_by_id("threshold-targetLow-input").clear()
                driver.find_element_by_id("threshold-targetLow-input").send_keys(str(contract.yellow_bottom).replace('.', ','))
                driver.find_element_by_id("threshold-targetLow-input").send_keys(Keys.TAB)

                actions = ActionChains(driver)
                actions.send_keys(str(contract.yellow_top).replace('.', ','))
                actions.send_keys(Keys.TAB)

                actions.send_keys(str(contract.red_bottom).replace('.', ','))
                actions.send_keys(Keys.TAB)

                actions.send_keys(str(contract.red_top).replace('.', ','))
                actions.send_keys(Keys.TAB)

                actions.perform()

                driver.find_element_by_id("26-reportSetting-interval-select").send_keys('1\n')

                # driver.find_element_by_id("save-Button").click()

                time.sleep(3)

                driver.find_element_by_id("reports-print-button").click()

                time.sleep(15)

                file = prepare_last_file()

                if file:
                    print("Got report")
                    attachments = [file]
                    medsenger_client.send_message(contract.id, "Отчет FreeStyleLibre", send_from='patient',
                                                  attachments=attachments)

                driver.back()
                driver.back()
            else:
                medsenger_client.send_message(contract.id, "Ошибка экспорта отчета FreeStyleLibre: пациент еще не открыл доступ к данным.", send_from='patient', only_doctor=True)
    driver.close()


def find_contract(contracts, name, birthday):
    for contract in contracts:
        if name in contract.name and contract.birthday == birthday:
            return contract
    return None


def prepare_last_file():
    for file in os.listdir(DOWNLOAD_PATH):
        if '.pdf' in file:
            prepared = prepare_file(DOWNLOAD_PATH + os.sep + file)
            os.remove(DOWNLOAD_PATH + os.sep + file)

            return prepared
    return None

def test_browser():
    driver = create_driver(True)

    driver.get("https://cardio.medsenger.ru")

    print(driver.page_source)