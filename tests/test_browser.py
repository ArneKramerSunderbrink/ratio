import os
import pytest
from flask import url_for
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.support.expected_conditions import url_to_be


@pytest.fixture
def browser():
    driver_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'driver', 'geckodriver')
    options = Options()
    options.headless = True
    driver = Firefox(options=options, executable_path=driver_path)

    yield driver

    driver.quit()


@pytest.mark.usefixtures('live_server')
def test_selenium(browser):  # todo this is just a temporary file to test how to run selenium
    wait = WebDriverWait(browser, 10)

    browser.get(url_for('tool.index', _external=True))
    wait.until(url_to_be(url_for('auth.login', next_url=url_for('tool.index'), _external=True) + '%3F'))
    content = browser.page_source

    assert 'Log In' in content
    #browser.find_element(By.NAME, 'q').send_keys('cheese' + Keys.RETURN)
    #first_result = wait.until(presence_of_element_located((By.CSS_SELECTOR, 'h3>div')))
    #print(first_result.get_attribute('textContent'))

    # todo run server local and visit my own side
