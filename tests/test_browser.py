import os
import pytest
from flask import url_for
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


@pytest.fixture
def browser():
    driver_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'driver', 'geckodriver')
    options = Options()
    options.headless = True
    driver = Firefox(options=options, executable_path=driver_path)
    driver.implicitly_wait(10)

    yield driver

    driver.quit()


@pytest.mark.usefixtures('live_server')
def test_header(browser):
    browser.get(url_for('tool.index', _external=True))
    browser.find_element(By.ID, 'username').send_keys('test')
    browser.find_element(By.ID, 'password').send_keys('test')
    browser.find_element(By.ID, 'password').send_keys(Keys.ENTER)
    # logged and redirected?
    assert browser.find_element(By.LINK_TEXT, 'Log Out')
    browser.find_element(By.LINK_TEXT, 'subgraph1').click()
    # redirected to /1?
    assert browser.find_element(By.ID, 'subgraph-name').text == 'subgraph1'
    # test toggling the overlay
    browser.find_element(By.ID, 'subgraph-name').click()
    assert browser.find_element(By.ID, 'overlay').is_displayed()
    browser.find_element(By.ID, 'subgraph-name').click()
    assert not browser.find_element(By.ID, 'overlay').is_displayed()
    browser.find_element(By.ID, 'subgraph-name').click()
    # test toggling the finished checkbox
    browser.find_element(By.CSS_SELECTOR, 'header > label[for="finished"]').click()
    assert browser.find_element(By.CSS_SELECTOR, 'div#subgraph-list input#finished-1').is_selected()
    browser.find_element(By.CSS_SELECTOR, 'div#subgraph-list label[for="finished-1"]').click()
    assert not browser.find_element(By.CSS_SELECTOR, 'header > input#finished').is_selected()
    # log out
    browser.find_element(By.ID, 'close-overlay').click()
    browser.find_element(By.LINK_TEXT, 'Log Out').click()
