from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

import app
from selenium.common.exceptions import WebDriverException, NoSuchElementException

from dotenv import load_dotenv
load_dotenv()
from csv import create_csv, find_or_create

from flask_mail import Message

from datetime import date
import csv
import time
import datetime
import io
import os
import re
import ssl
import urllib.request as r
ssl._create_default_https_context = ssl._create_unverified_context

# Creation of a new instance of Google Chrome
options = webdriver.ChromeOptions()
options.add_argument("--headless")
browser = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=options)

leads = []
all_managers = []
pm_data= [
    {"city": "GTA", "location_code": "90009551"},
    {"city": "London", "location_code": "102531267"},
    {"city": "Ottawa", "location_code": "106234700"},
    {"city": "Vancouver", "location_code": "103366113"},
    {"city": "Kingston", "location_code": "106374039"}
]

# Load the page on the browser
browser.get('https://www.linkedin.com/uas/login')

browser.execute_script(
    "(function(){try{for(i in document.getElementsByTagName('a')){let el = document.getElementsByTagName('a')[i]; "
    "if(el.innerHTML.includes('Sign in')){el.click();}}}catch(e){}})()"
)
time.sleep(5)
username = ''
password = ''
username_input = browser.find_element_by_id('username')
username_input.send_keys(username)
password_input = browser.find_element_by_id('password')
password_input.send_keys(password)
password_input.submit()
if not browser.current_url == "https://www.linkedin.com/feed/":
    print("Authentication Error: ", browser.current_url)
    time.sleep(40)

try:
    for i in range(25, 40):
        for url in pm_data:
            try:
                browser.get(f"https://www.linkedin.com/search/results/people/?geoUrn=%5B\"{url['location_code']}\"%5D&keywords=property%20manager&origin=FACETED_SEARCH&page={i}")
                elements = browser.find_elements_by_xpath('//*[@class="entity-result__title-text  t-16"]//a')
                for i in range(len(elements)):
                    all_managers.append(elements[i].get_attribute('href'))
                print(all_managers)
                if os.environ.get('TBC_TEST'):
                    break
            except Exception as e:
                print('this is what errored: ', e)

    for i in range(len(all_managers)):
        try:
            # if models.PropertyManagerLead.query.filter_by(url=all_managers[i]).one_or_none():
            #     continue
            # else:
            lead = {
                'url': f"{all_managers[i]}"
            }
            #put it all into functions
            #check for humanCheckException errors and if it is still on the desired page
            #check for identity verification
            browser.get(all_managers[i])
            time.sleep(1)
            lead['name'] = browser.find_element_by_xpath('//*[@class="inline t-24 t-black t-normal break-words"]').text
            try:
                lead['location'] = browser.find_element_by_xpath('//*[@class="t-16 t-black t-normal inline-block"]').text
            except:
                lead['location'] = None
            browser.execute_script("window.scrollTo(0,700)")
            time.sleep(1)
            firstExp = browser.find_element_by_xpath('(//*[@class="pv-entity__logo company-logo"]/img[1])[1]')
            if firstExp.get_attribute('alt') != None:
                lead['company'] = firstExp.get_attribute('alt')
                if firstExp.get_attribute("src") != "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7":
                    try:
                        companyUrl = browser.find_element_by_xpath('//*[@class="display-flex justify-space-between full-width"]/div/a').get_attribute('href')
                        browser.get(f"{companyUrl}about/")
                        try:
                            lead['company_employees'] = browser.find_element_by_xpath('//*[@class="org-about-company-module__company-size-definition-text t-14 t-black--light mb1 fl"]').text.split(" employees")[0]
                        except WebDriverException:
                            lead['company_employees'] = None
                            print("Error when finding company employees - ", e)
                    except NoSuchElementException as e:
                        companyUrl = browser.find_element_by_xpath('//*[@class="display-flex justify-space-between full-width"]/a').get_attribute('href')
                        browser.get(f"{companyUrl}about/")
                        try:
                            lead['company_employees'] = browser.find_element_by_xpath('//*[@class="org-about-company-module__company-size-definition-text t-14 t-black--light mb1 fl"]').text.split(" employees")[0]
                        except WebDriverException:
                            lead['company'] = None
                            lead['company_employees'] = None
                            print("Error when finding company employees: ", e)
                else:
                    lead['company_employees'] = None
            else:
                lead['company'] = None
                print("Could not find work experience")
                lead['company_employees'] = None
                #issue with num employees - most companies aren't established on linkedin (check photo for employment)
            lead['inserted_at'] = datetime.datetime.utcnow()
            print(" url: ", lead['url']," name: ", lead['name'], " company: ", lead['company'], " numEmployees: ", lead['company_employees'])
            if lead['company_employees'] and (lead['company_employees'] == '11-50' or lead['company_employees'] == '2-10'):
                leads.append(lead)
            else: 
                print('not inserted')
        except Exception as e:
            print("Errored while on user profile - ", e)
except Exception as e:
    print("Errored during PM search - ", e)
print('LEADS:\n', leads)
csv_pm_leads = create_csv(
    ['Name', 'Location', 'Url', 'Company', 'Company Employees','Inserted at'],
    [[i['name'], i['location'], i.get('url'), i['company'], i['company_employees'], i['inserted_at']] for i in leads if i['name'] and i['url']]
)
todays_date = date.today().strftime("%d/%m/%Y")
with app.app.app_context():
    msg = Message(
        f"Singlekey Sales Leads for {todays_date}",
        sender=os.environ['GMAIL_ACCOUNT'],
        recipients=['seb7wake@gmail.com'],
    )
    msg.html = f"Here are today's property managers. There are {len(leads)}"
    msg.attach(
        f"property_manager_leads_for_{todays_date}.csv", "text/csv", csv_pm_leads.getvalue()
    )
    print('email to sk dev team')
    app.mail.send(msg)