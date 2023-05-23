import random
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

DRIVER_OPTIONS = webdriver.ChromeOptions()
DRIVER_OPTIONS.add_argument("--incognito")
DRIVER_OPTIONS.add_argument('headless')
FILE_PATH = os.path.join(os.environ["USERPROFILE"], "Desktop") + '\cities_temperatures.txt'  #path to txt on users desktop

def set_viewport_size(driver, width, height):
    window_size = driver.execute_script("""
        return [window.outerWidth - window.innerWidth + arguments[0],
          window.outerHeight - window.innerHeight + arguments[1]];
        """, width, height)
    driver.set_window_size(*window_size)

def get_cities():
    """Returns the list of all the cities obtained from polskawliczbach.pl/Miasta"""
    popup_form_wait = 15
    driver = webdriver.Chrome(options=DRIVER_OPTIONS)
    set_viewport_size(driver, 1920, 1080)
    driver.get('https://www.polskawliczbach.pl/Miasta')

    # Waiting for cookies form and closing it
    try:
        WebDriverWait(driver, popup_form_wait).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.stpd_cmp > div > div')))
        private_form = driver.find_element(By.CSS_SELECTOR, 'body > div.stpd_cmp > div > div > div:nth-child(2) > div > button')
        private_form.click()
    except:
        print(f'No cookies form')
    # scrolling to table, waiting for dropdown to appear to show all cities
    cities_table = driver.find_element(By.CSS_SELECTOR, '#lstTab')
    ActionChains(driver).scroll_to_element(cities_table).perform()
    WebDriverWait(driver, popup_form_wait).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#lstTab_length > label > select')))
    dropdown_records_amount = Select(driver.find_element(By.CSS_SELECTOR, '#lstTab_length > label > select'))
    dropdown_records_amount.select_by_value('-1')
    # refreshing table and obtaining all cities
    cities_table = driver.find_element(By.CSS_SELECTOR, '#lstTab > tbody')
    cities_list = [row.find_element(By.CSS_SELECTOR,'a').text for row in cities_table.find_elements(By.CSS_SELECTOR, 'tr')]
    driver.quit()
    return cities_list

def cities_get_temperatures(cities_list):
    """Gets temperature of cities passed in a list from Google and saves it to cities_temperatures.txt file on desktop
       Returns list of cities for which temperature couldn't be obtained on Google"""
    popup_form_wait = 15
    cities_omitted = []
    with open(FILE_PATH, 'w', encoding='UTF-8') as f:
        reset = False
        i = 0
        while i < len(cities_list):
            city = cities_list[i]
            time.sleep(random.randint(10, 15) / 10)  # wait random number of time to avoid captcha
            # change session every 10 iterations or if something failed (possible captcha)
            if reset or i % 10 == 0:
                reset = False
                time.sleep(random.randint(5, 10) / 10)
                driv_options = webdriver.ChromeOptions()
                driv_options.add_argument("--incognito")
                driv_options.add_argument('headless')
                driver = webdriver.Chrome(options=driv_options)
                set_viewport_size(driver, 1920, 1080)
                driver.get('https://www.google.pl/')
                # Close possible cookies or agreements popup
                try:
                    WebDriverWait(driver, popup_form_wait).until(EC.presence_of_element_located((By.ID, 'CXQnmb')))
                    # private_form = driver.find_element(By.ID, 'W0wltc').click()
                    driver.find_element(By.ID, 'W0wltc').click()
                except:
                    print('No agreement form')
            else:
                driver.get('https://www.google.pl/')
            # Find and pass input to search box and press enter, or press search button. To avoid problems with
            # captcha, possible dropdown list or "enter" input mistakes, number of measures have been taken
            try:
                text_area = driver.find_element(By.ID, 'APjFqb')
                search_button = driver.find_element(By.CSS_SELECTOR, 'body > div.L3eUgb > div.o3j99.ikrT4e.om7nvf > form > div:nth-child(1)\
                                                             > div.A8SBwf > div.FPdoLc.lJ9FBc > center > input.gNO89b')
                text_area.send_keys(city + ' pogoda')
                ActionChains(driver).send_keys(Keys.ENTER).perform()
            except:
                # when text area couldn't be found most possibly there is a captcha form, session is restarted
                driver.quit()
                reset = True
                continue
            try:
                temperature = driver.find_element(By.ID,'wob_tm').text
            except:
                try:
                    # most possibly search hasn't been run, but lack of search button indicates captcha form
                    search_button.click()
                except:
                    driver.quit()
                    reset = True
                    continue
                try:
                    # if it wasn't captcha, it means that google didn't return the information, the city is added
                    # to the list of omitted cities to be processed later with other means
                    temperature = driver.find_element(By.ID, 'wob_tm').text
                except:
                    print(f"Couldn't get {city} temperature on Google")
                    cities_omitted.append(city)
                    i += 1
                    continue

            t = time.localtime()
            current_time = time.strftime("%Y-%m-%d %H:%M", t)
            f.write(f'{city} {temperature}°C {current_time} \n')
            i += 1
    return cities_omitted

def get_omitted_temperatures(cities_omitted):
    """Gets temperature for the cities that google didn't return information for. Information is obtained from
    pogoda.onet.pl. Cities are added to the cities_temperatures.txt file on desktop"""
    popup_form_wait = 15
    with open(FILE_PATH, 'a', encoding='UTF-8') as f:
        for city in cities_omitted:
            driver = webdriver.Chrome(options=DRIVER_OPTIONS)
            set_viewport_size(driver, 1920, 1080)
            driver.get('https://pogoda.onet.pl/')
            try:
                WebDriverWait(driver, popup_form_wait).until(EC.presence_of_element_located((By.ID, 'rasp_cmp')))
                private_form = driver.find_element(By.CSS_SELECTOR, '#rasp_cmp > div > div.cmp-intro_options > button.cmp-button_button.cmp-intro_acceptAll').click()
            except:
                print('No agreement form')

            time.sleep(2)
            text_area = driver.find_element(By.ID, 'locationSearch')
            text_area.send_keys(city)
            time.sleep(2)
            WebDriverWait(driver, popup_form_wait).until(EC.presence_of_element_located((By.ID, 'autocomplete-suggestions')))
            private_form = driver.find_element(By.CSS_SELECTOR, '#autocomplete-suggestions > div:nth-child(1)').click()
            # ActionChains(driver).send_keys(Keys.ENTER).perform()
            temperature = driver.find_element(By.CSS_SELECTOR,
                                              '#weatherMainWidget > div.widgetContent > div.underSearchBox >\
                                               div:nth-child(1) > div.widgetLeftCol > div.mainBox > div.mainBoxContent >\
                                               div.mainParams > div.temperature > div.temp').text.rstrip('°\n')
            t = time.localtime()
            current_time = time.strftime("%Y-%m-%d %H:%M", t)
            f.write(f'{city} {temperature}°C {current_time} \n')
            print(f'{city} temperature obtained from pogoda.onet.pl')


cities_list = get_cities()
cities_omitted = cities_get_temperatures(cities_list)

# adding additional option to avoid problems with notification on the Onet page
DRIVER_OPTIONS.add_experimental_option("prefs", { "profile.default_content_setting_values.geolocation": 2})
get_omitted_temperatures(cities_omitted)