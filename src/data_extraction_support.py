from bs4 import BeautifulSoup

import requests

import pandas as pd
import numpy as np

import time

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


### Acommodations - booking -scraping

def build_booking_url_full(destination: str, checkin: str, checkout: str, adults: int = 1, children: int = 0,
                           rooms: int = 1, min_price: int = 1, max_price: int = 1, star_ratings: list = None, 
                           meal_plan: str = None, review_score: list = None, max_distance_meters: int = None):
    """
    Build a Booking.com search URL by including all parameter filters, 
    ensuring proper formatting for all parameters.

    Parameters:
    - destination (str): Destination city.
    - checkin (str): Check-in date in YYYY-MM-DD format.
    - checkout (str): Check-out date in YYYY-MM-DD format.
    - adults (int): Number of adults.
    - children (int): Number of children.
    - rooms (int): Number of rooms.
    - min_price (int): Minimum price in Euros.
    - max_price (int): Maximum price in Euros.
    - star_ratings (list): List of star ratings (e.g., [3, 4, 5]).
    - meal_plan (int): Meal plan (0 for no meal, 1 for breakfast, etc.).
    - review_score (list): List of review scores (e.g., [80, 90] for 8.0+ and 9.0+).
    - max_distance_meters (int): Maximum distance from city center in meters (e.g., 500).

    Returns:
    - str: A Booking.com search URL based on the specified filters.
    """
    
    base_url = "https://www.booking.com/searchresults.es.html?"
    
    # Start with basic search parameters (ensure no tuple formatting)
    url = f"{base_url}ss={destination}&checkin={checkin}&checkout={checkout}&group_adults={adults}&group_children={children}&no_rooms={rooms}"
    
    
    if min_price is not None and max_price is not None:
        price_filter = f"price%3DEUR-{min_price}-{max_price}-1"
    elif min_price is not None:
        price_filter = f"price%3DEUR-{min_price}-1-1"
    elif max_price is not None:
        price_filter = f"price%3DEUR-{max_price}-1"
    else:
        price_filter = None

    # Construct 'nflt' parameter to add other filters
    nflt_filters = []
    
    if price_filter:
        nflt_filters.append(price_filter)
    
    if star_ratings:
        star_filter = '%3B'.join([f"class%3D{star}" for star in star_ratings])
        nflt_filters.append(star_filter)
    
    meal_plan_options = {
            "breakfast": 1,
            "breakfast_dinner": 9,
            "kitchen": 999,
            "nothing": None
        }
    meal_plan_formatted = meal_plan_options.get(meal_plan, None)

    if meal_plan_formatted is not None:
        meal_plan_str = f"mealplan%3D{meal_plan_formatted}"
        nflt_filters.append(meal_plan_str)
    
    if review_score:
        review_filter = '%3B'.join([f"review_score%3D{score}" for score in review_score])
        nflt_filters.append(review_filter)
    
    if max_distance_meters is not None:
        distance_str = f"distance%3D{max_distance_meters}"
        nflt_filters.append(distance_str)
    
    # Add all 'nflt' filters to URL
    if nflt_filters:
        url += f"&nflt={'%3B'.join(nflt_filters)}"
    
    return url

def scrape_accommodations_from_page(page_soup, verbose=False):
    accommodation_scraper_dict = {
        "name": lambda card: card.find("div",{"data-testid":"title"}).text,
        "url": lambda card: card.find("a",{"data-testid":"title-link"})["href"],
        "price_currency": lambda card: card.find("span",{"data-testid":"price-and-discounted-price"}).text.split()[0],
        "price_amount": lambda card: card.find("span",{"data-testid":"price-and-discounted-price"}).text.split()[1].replace(".","").replace(",","."),
        "distance_city_center_km": lambda card: card.find("span",{"data-testid":"distance"}).text.split()[1].replace(".","").replace(",","."),
        "close_to_metro": lambda card: "Yes" if card.find("span",{"class":"f419a93f12"}) else "No",
        "sustainability_cert": lambda card: "Yes" if card.find("span",{"class":"abf093bdfe e6208ee469 f68ecd98ea"}) else "No",
        "room_type": lambda card: card.find("h4",{"class":"abf093bdfe e8f7c070a7"}).text,
        "double_bed": lambda card: "Yes" if any(["doble" in element.text for element in card.find_all("div",{"class":"abf093bdfe"})]) else "No",
        "single_bed": lambda card: "Yes" if any(["individual" in element.text for element in card.find_all("div",{"class":"abf093bdfe"})]) else "No",
        "free_cancellation": lambda card: "Yes" if any([element.text == "Cancelación gratis" for element in card.find_all("div",{"class":"abf093bdfe d068504c75"})]) else "No",
        "breakfast_included": lambda card: "Yes" if any([element.text == "Cancelación gratis" for element in card.find_all("div",{"class":"abf093bdfe d068504c75"})]) else "No",
        "pay_at_hotel": lambda card: "Yes" if any(['Sin pago por adelantado' in element.text for element in card.find_all("div",{"class":"abf093bdfe d068504c75"})]) else "No",
        "location_score": lambda card: card.find("span",{"class":"a3332d346a"}).text.split()[1].replace(",","."),
        "free_taxi": lambda card: "Yes" if any(["taxi gratis" in element.text.lower() for element in card.find_all("div",{"span":"b30f8eb2d6"})]) else "No"
    }

    accommodation_data_dict = {key: [] for key in accommodation_scraper_dict}

    for accommodation_card in soup.findAll("div", {"aria-label":"Alojamiento"}):
            for key, accommodation_scraper_function in accommodation_scraper_dict.items():
                try:
                    accommodation_data_dict[key].append(accommodation_scraper_function(accommodation_card))
                except Exception as e:
                    if verbose == True:
                        print(f"Error filling {key} due to {e}")
                    accommodation_data_dict[key].append(np.nan)

    return accommodation_data_dict


# dynamic html loading functions
def scroll_to_bottom(driver):
    last_height = driver.execute_script("return window.pageYOffset")

    while True:

        driver.execute_script('window.scrollBy(0, 2000)')
        time.sleep(0.2)
        
        new_height =  driver.execute_script("return window.pageYOffset")
        if new_height == last_height:
            break
        last_height = new_height

def scroll_back_up(driver):
    driver.execute_script('window.scrollBy(0, -600)')
    time.sleep(0.2)

def click_load_more(driver, css_selector):
    try:
        button = driver.find_element("xpath",'//*[@id="bodyconstraint-inner"]/div[2]/div/div[2]/div[3]/div[2]/div[2]/div[3]/div[*]/button')
        button.click()
        return True
    except:
        return print("'Load more' not found")

def scroll_and_click_cycle(driver, css_selector):
    while True:
        scroll_to_bottom(driver)
        scroll_back_up(driver)
        if not click_load_more(driver, css_selector):
            break


def extract_all_activities(destination: str, checkin: str, checkout: str, adults: int = 1, children: int = 0,
                           rooms: int = 1, min_price: int = 1, max_price: int = 1, star_ratings: list = None, 
                           meal_plan: str = None, review_score: list = None, max_distance_meters: int = None, verbose=False):
    accommodation_link = build_booking_url_full(
        destination=destination,
        checkin=checkin,
        checkout=checkout,
        adults=adults, 
        children=children, 
        rooms=rooms, 
        max_price=max_price, 
        star_ratings=star_ratings, 
        meal_plan=meal_plan,  
        review_score=review_score,  
        max_distance_meters=max_distance_meters 
    )

    # open driver
    driver = webdriver.Chrome()
    driver.maximize_window()
    driver.get(accommodation_link)

    # scroll and load more until bottom
    css_selector = "#bodyconstraint-inner > div:nth-child(8) > div > div.af5895d4b2 > div.df7e6ba27d > div.bcbf33c5c3 > div.dcf496a7b9.bb2746aad9 > div.d4924c9e74 > div.c82435a4b8.f581fde0b8 > button"
    scroll_and_click_cycle(driver, css_selector)

    # parse and get accommodations info
    html_page = driver.page_source

    page_soup = BeautifulSoup(html_page, "html.parser")
    
    total_accommodation_df = pd.DataFrame(scrape_accommodations_from_page(page_soup,verbose=verbose))

    return total_accommodation_df
    

### Activities - civitatis

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


def scrape_activities_from_page(page_soup, verbose=False):
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

            "activity_name": lambda element: element.find("a", {"class": "ga-trackEvent-element _activity-link"})["title"],

            "description": lambda element: element.find("div", {"class": "comfort-card__text l-list-card__text"}).text.strip().replace("\xa0", " "),

            "url": lambda element: "www.civitatis.com" + element.find("a",{"data-eventcategory":"Actividades Listado"})["href"],

            # image/gif
            "image": lambda element: "www.civitatis.com" + element.find("img")["src"],

            # image/gif
            "image2": lambda element: "www.civitatis.com" + element.find("img")["data-src"],

            # NOTE_: I'LL HAVE TO HANDLE LAST AND FIRST DAYS OF MONTH CAREFULLY, AS MONTH NOT SPECIFIED
            "available_days": lambda _: [el.find('br').next_sibling.strip() for el in availability_cards],
            
            "available_times": lambda _: [[time.text for time in el.find_all("span", {"class": "_time"})] for el in availability_cards],
            
            "duration": lambda element: element.find("div", {"class": "comfort-card__features"}).findAll("span")[0].text.strip(),
            
            # address: use latitude and longitude, then convert with geopy
            "latitude": lambda element: element.find("article", recursive=False)["data-latitude"],
            "longitude": lambda element: element.find("article", recursive=False)["data-longitude"],

            "address": lambda element: geolocator.reverse(
                (element.find("article", recursive=False)["data-latitude"], 
                element.find("article", recursive=False)["data-longitude"])
            ).address,
    
            "price": lambda element: json.loads(element.find("a", {"class": "ga-trackEvent-element _activity-link"})["data-gtm-new-model-click"])["ecommerce"]["click"]["products"][0]["price"],
            
            "currency": lambda element: json.loads(element.find("a", {"class": "ga-trackEvent-element _activity-link"})["data-gtm-new-model-click"])["ecommerce"]["currencyCode"],
            
            "category": lambda element: element.find("div", {"class": "comfort-card__features"}).findAll("span")[1].text.strip(),
        }
        
        

        for key, activity_scraper_function in activity_scraper_dict.items():
            try:
                activity_data_dict[key].append(activity_scraper_function(element))
                
            except Exception as e:
                if verbose == True:
                    print(f"Error filling {key} due to {e}")
                activity_data_dict[key].append(np.nan)

    return activity_data_dict





def extract_all_activities(city_name, date_start, date_end, verbose=False):
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

    soup = BeautifulSoup(html_content1, "html.parser")

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

        page_soup = BeautifulSoup(page_html, "html.parser")
        page_activities_df = pd.DataFrame(scrape_activities_from_page(page_soup, verbose=verbose))
        total_actitivities_df = pd.concat([total_actitivities_df,page_activities_df]).reset_index(drop=True)
        

    return total_actitivities_df


