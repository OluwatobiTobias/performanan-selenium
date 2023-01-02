from concurrent.futures import ThreadPoolExecutor, wait as Wait, as_completed
from selenium import webdriver
from os import getcwd, path

def driver_setup() -> webdriver:
    driver_path = path.join(getcwd(), 'chromedriver')
    options = webdriver.ChromeOptions()
    
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(executable_path=driver_path, options=options)
    return driver


def scraping(driver:webdriver, url:str) -> None:
    driver.get(url)
    c = driver.title
    # print(f"\n TITLE IS --- {c}")
    driver.quit()
    return c

# def call()

list_of_urls = ['https://superfastpython.com/', 
'https://github.com/OluwatobiTobias/automation-webscrapping-with-selenium/blob/chef/imperial.py', 
'https://stackoverflow.com/questions/59387309/multithreading-in-python-selenium',
'https://beautiful-soup-4.readthedocs.io/en/latest/#searching-the-tree'
]

with ThreadPoolExecutor() as executor:
    futures = [executor.submit(scraping, driver_setup(), url).add_done_callback() for url in list_of_urls]
    # futures, _ = Wait([executor.submit(scraping,driver_setup(), url) for url in list_of_urls])
    print('-------------line after thread already executed------------------')
    for future in as_completed(futures):
        print(future.result())
    print('DONE')
    
    


