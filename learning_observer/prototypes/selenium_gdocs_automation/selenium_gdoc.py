'''
This is a script to log into Google Docs, and eventually do a
little bit of typing.

This should not be used with your main Google account.

For this to work, you will need to enable "Less secure app access."

And then it still won't work... It's cat-and-mouse

https://sqa.stackexchange.com/questions/42307/trying-to-login-to-gmail-with-selenium-but-this-browser-or-app-may-not-be-secur
https://stackoverflow.com/questions/60117232/selenium-google-login-block
https://stackoverflow.com/questions/57602974/gmail-is-blocking-login-via-automation-selenium

undetected_chromedriver seems to work right now, but might stop tomorrow.
'''

import os
import random
import sys
import time

import undetected_chromedriver.v2 as uc
from selenium.webdriver.common.keys import Keys

# I haven't validated this URL, and it should NOT be used in production unless
# it's confirmed to be a Google thing. I think it is, but I'm not sure.

PLAYGROUND_OAUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth/" \
    "oauthchooseaccount?redirect_uri=https%3A%2F%2Fdevelopers.google.com%" \
    "2Foauthplayground&prompt=consent&response_type=code&" \
    "client_id=407408718192.apps.googleusercontent.com&scope=email&" \
    "access_type=offline&flowName=GeneralOAuthFlow"

chrome_options = uc.ChromeOptions()

chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--profile-directory=Default")
chrome_options.add_argument("--ignore-certificate-errors")
chrome_options.add_argument("--disable-plugins-discovery")
chrome_options.add_argument("--incognito")
chrome_options.add_argument("user_agent=DN")
driver = uc.Chrome(options=chrome_options)

driver.delete_all_cookies()

driver.get(PLAYGROUND_OAUTH_URL)

USERNAME_XPATH = "/html/body/div[1]/div[1]/div[2]/div/div[2]/div/div/div[2]" \
    "/div/div[1]/div/form/span/section/div/div/div[1]/div/div[1]/div/div[1]" \
    "/input"

PASSWORD_XPATH = "/html/body/div[1]/div[1]/div[2]/div/div[2]/div/div/div[2]/" \
    "div/div[1]/div/form/span/section/div/div/div[1]/div/div[1]/div/div[1]/input"

print("Username: ")
driver.find_element_by_xpath(USERNAME_XPATH).send_keys(input())
driver.find_element_by_xpath(PASSWORD_XPATH).send_keys(Keys.RETURN)


# Old (non-working) version:

# import selenium.webdriver
# import time
# from selenium.webdriver.chrome.options import Options
# from selenium_stealth import stealth

# chrome_options = Options()
# chrome_options.add_argument('--disable-useAutomationExtension')
# chrome_options.add_argument("--disable-popup-blocking")
# chrome_options.add_argument("--profile-directory=Default")
# chrome_options.add_argument("--disable-plugins-discovery")
# chrome_options.add_argument("--disable-web-security")
# chrome_options.add_argument("--allopw-running-insecure-content")
# chrome_options.add_argument("--incognito")
# chrome_options.add_argument("user_agent=DN")
# chrome_options.add_experimental_option("excludeSwitches",
#    ["enable-automation"])
# chrome_options.add_experimental_option('useAutomationExtension', False)

# driver = selenium.webdriver.Chrome(options=chrome_options)
# stealth(driver,
#         languages=["en-US", "en"],
#         vendor="Google Inc.",
#         platform="Win32",
#         webgl_vendor="Intel Inc.",
#         renderer="Intel Iris OpenGL Engine",
#         fix_hairline=True,
# )

# def documentready():
#     return driver.execute_script('return document.readyState;') == 'complete'

# driver.get(PLAYGROUND_OAUTH_URL)

# while not documentready():
#     time.sleep(0.1)

# time.sleep(1)

# ets = driver.find_elements_by_css_selector("input")
# et = [e for e in ets if e.get_attribute("aria-label") == 'Email or phone'][0]
# et.send_keys()

# btns = driver.find_elements_by_css_selector("button")
# btn = [b for b in btns if b.text == 'Next'][0]
# btn.click()

# #driver.get("http://docs.google.com")
