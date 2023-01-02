from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (NoSuchElementException,
                                        StaleElementReferenceException,
                                        TimeoutException)
from typing import NoReturn, List, Tuple, Dict
from os import path, getcwd
from time import sleep
import re


driver_path = path.join(getcwd(), 'chromedriver')
options = webdriver.ChromeOptions()

prefs = {"profile.managed_default_content_settings.images": 2}
options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(executable_path=driver_path, options=options)

@dataclass
class ScrapeEvent:
    """ 
    The codebase design uses a single Class( dataclass) with it Methods as function scraping singular data (some more though).
    Returns the "self" to a it caller which is handled by a context manager.
    """

    browser: WebDriver = driver
    
    def __enter__(self) -> NoReturn:
        "Handles the contex manager."
        return self

    def __exit__(self, exc_type=None, exc_value=None, exc_tb=None) -> NoReturn:
        "Hanles the teardown of the context manager."
        self.browser.quit()

    def dispatch(self, locator:str, strategy:webdriver = By.CSS_SELECTOR):
        "Call to selenium.webdriver.remote.webelement.WebElement.find_element()"
        return self.browser.find_element(strategy, locator)

    def dispatchList(self, locator:str, strategy: webdriver = By.CSS_SELECTOR):
        "Call to selenium.webdriver.remote.webelement.WebElement.find_elements()"
        return self.browser.find_elements(strategy, locator)

    def get_events(self, url: str) -> NoReturn:
        "Returns a list of all urls"
        self.browser.get(url)
        sleep(3)

    def scrape_listing_page(self) -> List[str]:

        container:list = []

        event_type = [i.text for i in self.dispatchList('.col.event.xs-12 .feature.topic')]
        event_name = [i.text for i in self.dispatchList('.col.event.xs-12 .title')]
        event_venue = [i.text for i in self.dispatchList('.col.event.xs-12 .venue')]
        event_start_date = [re.split(r"[+T]", i.get_attribute('datetime'))[:1] for i in self.dispatchList('.col.event.xs-12 .date [datetime]:nth-child(1)')]
        event_end_date = [re.split(r"[+T]", i.get_attribute('datetime'))[:1] for i in self.dispatchList('.col.event.xs-12 .date [datetime]:nth-child(2)')]
        event_url = [i.get_attribute('href') for i in self.dispatchList('.col.event.xs-12 a')]

        for i in zip(event_url, event_name, event_venue, event_type, event_start_date, event_end_date):
            print(i)
    

    def get_event(self, url: str) -> NoReturn:
        "Get a singualr event from a list of all events"
        try:
            self.browser.get(url)
        except Exception as e:
            self.error_msg_from_class += '\n' + str(e)
            logger.error(f'{self.click_event.__name__} Function failed', exc_info=True)


    def event_timing(self) -> json:
        "Scrapes and return a JSONified format of event timing."
        try:
            sc_event_timing = self.browser.find_element(By.CSS_SELECTOR, '.event-details__time--local').text
        except Exception as e:
            self.error_msg_from_class += '\n' + str(e)
            logger.error(f'{self.event_timing.__name__} Function failed', exc_info=True)
        else:
            match = re.search("(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})\s?(\w{3}|\w{2})", sc_event_timing.strip())
            if match:
                return json.dumps([
                        dict(type='general',
                            Start_time=datestrptime(match.group(1),'%H:%M').strftime('%I:%M%p'),
                            end_time=datestrptime(match.group(2),'%H:%M').strftime('%I:%M%p'),
                            timezone=match.group(3),
                            days='all')])
            else:
                return ''

    
    def event_info(self) -> str:
        "Scrapes and return event info."
        try:
            sc_event_info = self.browser.find_element(By.CSS_SELECTOR, '.module.content-hero__body p').text
        except NoSuchElementException: pass
        except Exception as e:
            self.error_msg_from_class += '\n' + str(e)
            logger.error(f'{self.event_info.__name__} Function failed', exc_info=True)
        else:
            match = re.search('(^.+?\.)', sc_event_info.replace('\n', '').strip())
            if match:
                return match.group(1)
            else:
                try:
                    sc_event_info = self.browser.find_element(By.CSS_SELECTOR, '.module.content-hero__body p:nth-child(3)').text
                except NoSuchElementException: pass
                except Exception as e:
                    self.error_msg_from_class += '\n' + str(e)
                    logger.error(f'{self.event_info.__name__} Function failed', exc_info=True)
                else:
                    if sc_event_info:
                        return sc_event_info
                    else:
                        return ''
        

    def event_ticket_list(self) -> json:
        "Scrapes and return a JSONified format of event timing."
        try:
            sc_event_ticket_list = self.browser.find_element(By.CSS_SELECTOR, '.event-details__label + span').text
        except Exception as e:
            self.error_msg_from_class += '\n' + str(e)
            logger.error(f'{self.event_ticket_list.__name__} Function failed', exc_info=True)
        else:
            if 'free' in sc_event_ticket_list.lower().strip():
                return json.dumps([dict(type='free', price='', currency='')])
            else:
                return json.dumps([dict(type='paid', price=sc_event_ticket_list[1:], currency=sc_event_ticket_list[0])], ensure_ascii=False)


    def event_mode(self, mode_type: str, event_name: str) -> Tuple[str, str]:
        "Scrapes and return event venue "
        if 'online' in mode_type.lower() or 'webinar' in mode_type.lower() or 'webinar' in event_name.lower() or 'webinar' in event_name.lower():  
            return 'ONLINE'

        if ',' in mode_type:
            if len(mode_type.split(',')) < 3:
                venue, city = mode_type, ''
                return venue, city
                

            elif len(mode_type.split(',')) == 3:
                venue, city = ''.join(mode_type.split(',')[:2]), ''.join(mode_type.split(',')[2])
                return venue, city            

            elif len(mode_type.split(',')) > 3:
                venue, city = ''.join(mode_type.split(',')[:2]), '' 
                return venue, city
            else:
                return mode_type, ''
                
        else:
            return mode_type, ''


    def contactmail(self) -> json:
        try:
            sc_event_contactmail = self.browser.find_elements(By.CSS_SELECTOR, ' .event-details__label + a')
            sc_event_contactmail = [i.get_attribute('href') for i in sc_event_contactmail]
        except Exception as e:
            self.error_msg_from_class += '\n' + str(e)
            logger.error(f'{self.event_ticket_list.__name__} Function failed', exc_info=True)
        else:
            container: List[str] = []
            for i in sc_event_contactmail:
                if '@' not in i:
                    pass
                else:
                    container.append(i.replace('mailto:', ''))
            
            return json.dumps(container, ensure_ascii=False)


    def event_speakerlist(self) -> json:
        "Scrapes and return a JSONified format of event speaker_list."
        try:
            speaker  = self.browser.find_element(By.CSS_SELECTOR, '.event-details .event-details__list-content h4').text
        except NoSuchElementException or Exception as e:
            speaker = ''
            self.error_msg_from_class += '\n' + str(e)
            logger.error(f'{self.event_ticket_list.__name__} Function failed', exc_info=True)

        try:
            link = self.browser.find_element(By.CSS_SELECTOR, '.event-details .event-details__list-content h4 a').get_attribute('href')
        except NoSuchElementException or Exception as e:
            link = ''
            self.error_msg_from_class += '\n' + str(e)
            logger.error(f'{self.event_ticket_list.__name__} Function failed', exc_info=True)
            
        try:
            title = self.browser.find_element(By.CSS_SELECTOR, '.event-details__block--speakers .event-details__value').text
        except NoSuchElementException or Exception as e:
            title = ''
            self.error_msg_from_class += '\n' + str(e)
            logger.error(f'{self.event_ticket_list.__name__} Function failed', exc_info=True)

        if speaker:
            if title is None or str(title) == 'None':
                title = ''
            if link is None or str(link) == 'None':
                link = ''
            return json.dumps([dict(name=speaker, title=title, link=link)], ensure_ascii=False)
        else:
            return ''


    def google_map_url(self, search_word: str) -> str:
        """
        Returns the result of a Google Maps location search of the parameter.
        This implementation creates a new tab for it job, closes it when done and switch back handle to previous tab.
        """
        try:
            if search_word == 'ONLINE':
                return 'ONLINE'

            curr_tab = self.browser.current_window_handle
            self.browser.switch_to.new_window('tab')

            self.browser.get('http://google.com')
            search = self.wait_5sec.until(
                EC.presence_of_element_located((By.NAME, 'q')))

            search.send_keys(search_word)
            search.send_keys(Keys.RETURN)

            map_url = WebDriverWait(self.browser, 3).until(
                EC.element_to_be_clickable((By.LINK_TEXT, 'Maps')))
            map_url.click()
            sleep(0.5)
            map_url = self.browser.current_url
        
        except Exception as e:
            self.error_msg_from_class += '\n' + str(e)
            logger.error(f'{self.google_map_url.__name__} Function failed', exc_info=True)

        else:
            self.browser.close()
            self.browser.switch_to.window(curr_tab)
            return map_url