from bs4 import BeautifulSoup

import requests

import pandas as pd
import numpy as np

from time import sleep

from selenium import webdriver 
from webdriver_manager.chrome import ChromeDriverManager  
from selenium.webdriver.common.keys import Keys  
from selenium.webdriver.support.ui import Select 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException 

from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="my-geopy-app")
import random
import re
import datetime
import json
import math

# import suppor functions
import sys 
sys.path.append("..")




def get_pagination_htmls_by_city_date(city_name, date_start, date_end, page_start, n_pages, driver):

    html_contents = list()

    for page_number in range(page_start, n_pages + page_start):

        activities_link = f"https://www.civitatis.com/es/{city_name}/?page={page_number}&fromDate={date_start}&toDate={date_end}"

        driver.get(activities_link)
        driver.maximize_window()
        
        driver.implicitly_wait(20)
        driver.execute_script('window.scrollBy(0, 4000)')
        driver.find_element("css selector","div.m-availability")
        

        html_content = driver.page_source

        html_contents.append(html_content)

    return html_contents


def scrape_activities_from_page(page_soup):
    activity_data_dict = {
            "activity_name": [],
            "description": [],
            "url": [],
            "image": [],
            "image2": [],
            "available_days": [],
            "available_times": [],
            "duration": [],
            "latitude": [],
            "longitude": [],
            "address": [],
            "price": [],
            "currency": [],
            "category": []
    }
    for element in page_soup.findAll("div",{"class","o-search-list__item"}):

        availability_cards = list(set(element.findAll("div", {"class": "m-availability__item"})) - 
                                set(element.findAll("div", {"class": "m-availability__item _no-dates"})))
        

        activity_scraper_dict = {
            # activity name
            "activity_name": lambda element: element.find("a", {"class": "ga-trackEvent-element _activity-link"})["title"],
            
            # description
            "description": lambda element: element.find("div", {"class": "comfort-card__text l-list-card__text"}).text.strip().replace("\xa0", " "),

            # url 
            "url": lambda element: "www.civitatis.com" + element.find("a",{"data-eventcategory":"Actividades Listado"})["href"],

            # image/gif
            "image": lambda element: "www.civitatis.com" + element.find("img")["data-src"],

            # image/gif
            "image2": lambda element: "www.civitatis.com" + element.find("img")["src"],

            # find available days. NOTA: ILL HAVE TO HANDLE LAST AND FIRST DAYS OF MONTH CAREFULLY
            "available_days": lambda _: [el.find('br').next_sibling.strip() for el in availability_cards],
            
            # available times per day
            "available_times": lambda _: [[time.text for time in el.find_all("span", {"class": "_time"})] for el in availability_cards],
            
            # duration
            "duration": lambda element: element.find("div", {"class": "comfort-card__features"}).findAll("span")[0].text.strip(),
            
            # address: use latitude and longitude, then convert with geopy
            "latitude": lambda element: element.find("article", recursive=False)["data-latitude"],
            "longitude": lambda element: element.find("article", recursive=False)["data-longitude"],

            "address": lambda element: geolocator.reverse(
                (element.find("article", recursive=False)["data-latitude"], 
                element.find("article", recursive=False)["data-longitude"])
            ).address,
    
            # price
            "price": lambda element: json.loads(element.find("a", {"class": "ga-trackEvent-element _activity-link"})["data-gtm-new-model-click"])["ecommerce"]["click"]["products"][0]["price"],
            
            # price currency
            "currency": lambda element: json.loads(element.find("a", {"class": "ga-trackEvent-element _activity-link"})["data-gtm-new-model-click"])["ecommerce"]["currencyCode"],
            
            # category 
            "category": lambda element: element.find("div", {"class": "comfort-card__features"}).findAll("span")[1].text.strip(),
        }


        for key, activity_scraper_function in activity_scraper_dict.items():
            try:
                activity_data_dict[key].append(activity_scraper_function(element))
                
            except Exception as e:
                print(f"Error filling {key} due to {e}")
                activity_data_dict[key].append(np.nan)

    return activity_data_dict


def extract_all_activities(city_name, date_start, date_end):
    # define url 
    first_link = f"https://www.civitatis.com/es/{city_name}/?fromDate={date_start}&toDate={date_end}"

    # open driver
    driver = webdriver.Chrome()
    driver.maximize_window()
    driver.get(first_link)

    # make sure availability cards and amount of available activities show in the page
    driver.implicitly_wait(20)
    driver.find_element("css selector","div.m-availability")
    driver.find_element("css selector","#activitiesShowing")

    # parse first page to get last page number
    html_content1 = driver.page_source

    soup = BeautifulSoup(html_content1)

    last_page = math.ceil(int(soup.find("div",{"class","columns o-pagination__showing"}).find("div",{"class":"left"}).text.split()[0])/20)
    last_page

    page_start = 2
    n_pages = last_page - 1

    # collect unparsed pages html
    html_contents = get_pagination_htmls_by_city_date(city_name, date_start, date_end, page_start, n_pages, driver)
    html_contents.append(html_content1)

    # parse each page and scrape elements
    total_actitivities_df = pd.DataFrame()
    for page_html in html_contents:

        page_soup = BeautifulSoup(page_html)
        page_activities_df = pd.DataFrame(scrape_activities_from_page(page_soup))
        total_actitivities_df = pd.concat([total_actitivities_df,page_activities_df]).reset_index(drop=True)
        

    total_actitivities_df


