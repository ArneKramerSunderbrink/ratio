import os
import pytest
from flask import url_for
from selenium.webdriver import Firefox
from selenium.webdriver import ActionChains
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec


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
@pytest.mark.usefixtures("reset_db")
def test_header(browser):
    wait = WebDriverWait(browser, 5)

    # log in
    browser.get(url_for('tool.index', _external=True))
    browser.find_element(By.ID, 'username').send_keys('test')
    browser.find_element(By.ID, 'password').send_keys('test')
    browser.find_element(By.ID, 'password').send_keys(Keys.ENTER)
    # logged in and redirected?
    wait.until(ec.url_to_be(url_for('tool.index', _external=True)))
    assert browser.find_element(By.LINK_TEXT, 'Log Out')

    # go to /1
    browser.find_element(By.LINK_TEXT, 'subgraph1').click()
    wait.until(ec.url_to_be(url_for('tool.index', subgraph_id=1, _external=True)))
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


@pytest.mark.usefixtures('live_server')
@pytest.mark.usefixtures("reset_db")
def test_subgraph_list(browser):
    wait = WebDriverWait(browser, 5)

    # log in
    browser.get(url_for('tool.index', _external=True))
    browser.find_element(By.ID, 'username').send_keys('test')
    browser.find_element(By.ID, 'password').send_keys('test')
    browser.find_element(By.ID, 'password').send_keys(Keys.ENTER)
    # logged in and redirected?
    wait.until(ec.url_to_be(url_for('tool.index', _external=True)))
    assert browser.find_element(By.LINK_TEXT, 'Log Out')

    # test the filter
    item = browser.find_element(By.CSS_SELECTOR, 'div.item[data-subgraph-id="2"]')
    assert item.is_displayed()
    filter_input = browser.find_element(By.ID, 'subgraph-filter')
    ActionChains(browser).send_keys_to_element(filter_input, '1').key_up('1').perform()
    assert not item.is_displayed()

    # go to /1
    browser.find_element(By.LINK_TEXT, 'subgraph1').click()
    wait.until(ec.url_to_be(url_for('tool.index', subgraph_id=1, _external=True)))
    assert browser.find_element(By.ID, 'subgraph-name').text == 'subgraph1'

    # test change subgraph name to empty
    browser.find_element(By.ID, 'subgraph-name').click()
    item = browser.find_element(By.CSS_SELECTOR, 'div.item[data-subgraph-id="1"]')
    item.find_element(By.CSS_SELECTOR, 'a.flip-flipbutton').click()
    item.find_element(By.CSS_SELECTOR, 'form input[name="name"]').clear()
    item.find_element(By.CSS_SELECTOR, 'form input[name="name"]').send_keys('   ')
    item.find_element(By.CSS_SELECTOR, 'form button[type="submit"]').click()
    wait.until(ec.visibility_of(browser.find_element(By.ID, 'subgraph-menu-edit-msg')))
    assert browser.find_element(By.ID, 'subgraph-menu-edit-msg').text == 'Subgraph name cannot be empty.'

    # test change subgraph name to new name
    item.find_element(By.CSS_SELECTOR, 'form input[name="name"]').clear()
    item.find_element(By.CSS_SELECTOR, 'form input[name="name"]').send_keys('new name')
    item.find_element(By.CSS_SELECTOR, 'form button[type="submit"]').click()
    wait.until(ec.text_to_be_present_in_element((By.CSS_SELECTOR, 'div#subgraph-list a[href="/1"]'), 'new name'))
    assert browser.find_element(By.ID, 'subgraph-name').text == 'new name'

    # test delete subgraph
    item.find_element(By.CSS_SELECTOR, 'a.flip-flipbutton').click()
    item.find_element(By.CSS_SELECTOR, 'a.delete-subgraph-button').click()
    div_message = browser.find_element(By.CSS_SELECTOR, 'div#subgraph-menu-delete-msg')
    wait.until(ec.visibility_of(div_message))
    assert div_message.find_element(By.CSS_SELECTOR, 'span').text == '"new name" has been deleted.'
    assert not item.is_displayed()
    assert not browser.find_element(By.ID, 'close-overlay').is_displayed()

    # test undo delete
    browser.find_element(By.LINK_TEXT, 'Undo.').click()
    wait.until(ec.visibility_of(browser.find_element(By.ID, 'close-overlay')))
    assert browser.find_element(By.ID, 'close-overlay').is_displayed()
    assert item.is_displayed()

    # test add subgraph
    browser.find_element(By.CSS_SELECTOR, 'button[data-flipid="new-subgraph"]').click()
    browser.find_element(By.ID, 'new-subgraph-name').send_keys('new subgraph')
    browser.find_element(By.CSS_SELECTOR, 'form#new-subgraph-form button[type="submit"]').click()
    # redirect to new subgraph
    wait.until(ec.url_to_be(url_for('tool.index', subgraph_id=5, _external=True)))
    assert browser.find_element(By.ID, 'subgraph-name').text == 'new subgraph'
    browser.find_element(By.ID, 'subgraph-name').click()
    assert browser.find_element(By.LINK_TEXT, 'new subgraph')

    # log out
    browser.find_element(By.LINK_TEXT, 'Log Out').click()
