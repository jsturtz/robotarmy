'''
Put any tools for doing browser manipulation here
'''

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
import re

class Actions(ActionChains):
    def wait(self, time_s: float):
        self._actions.append(lambda: time.sleep(time_s))
        return self

def safely_click(driver, elem):
    driver.execute_script("arguments[0].scrollIntoView();", elem)
    #time.sleep(0.5)
    WebDriverWait(driver, 10).until(EC.visibility_of(elem))
    elem.click()

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
