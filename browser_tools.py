'''
Put any tools for doing browser manipulation here
'''

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyperclip

import time
import re

class Actions(ActionChains):
    def wait(self, time_s: float):
        self._actions.append(lambda: time.sleep(time_s))
        return self

def safely_click(driver, elem):
    driver.execute_script("arguments[0].scrollIntoView();", elem)
    WebDriverWait(driver, 10).until(EC.visibility_of(elem))
    driver.execute_script("arguments[0].click()", elem)
    # FIXME: THIS BULLSHIT HAS TO END
    # elem.click()

def send_keys(driver, elem, s):
    pyperclip.copy(s)
    elem.send_keys(Keys.LEFT_CONTROL, 'v')

def get_text_excluding_children(driver, element):
    return driver.execute_script("""
        var parent = arguments[0];
        var child = parent.firstChild;
        var ret = "";
        while(child) {
            if (child.nodeType === Node.TEXT_NODE)
                ret += child.textContent;
            child = child.nextSibling;
        }
        return ret;
    """, element)

def replace_newlines(s):
    return s.replace('\\n', Keys.ENTER)

def element_exists(driver, by, identifier):
    driver.implicitly_wait(1)
    try:
        driver.find_elements(by, identifier)
        driver.implicitly_wait(10)
        return True
    except:
        driver.implicitly_wait(10)
        return False
