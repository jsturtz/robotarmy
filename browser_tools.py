'''
Put any tools for doing browser manipulation here
'''

from selenium.webdriver.common.action_chains import ActionChains

def move_and_click(driver, elem):
    actions = ActionChains(driver)
    actions.move_to_element(elem).perform()
    actions.click(elem).perform()

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
