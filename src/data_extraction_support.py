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
import random
import re
import datetime
import json
import math
import dotenv
import os

dotenv.load_dotenv()

AIR_SCRAPPER_API_KEY = os.getenv("AIR_SCRAPPER_KEY")
geolocator = Nominatim(user_agent="my-geopy-app")

def map_airport_codes(dictionary: dict, country: str) -> dict:
    """
    Maps airport codes and details from a response dictionary.
    
    Parameters:
    - dictionary (dict): A dictionary containing airport data.
    - country (str): The country name.
    
    Returns:
    - dict: A dictionary with mapped airport details.
    """
    navigation = dictionary["navigation"]
    result_dict = {"country": country}

    result_dict_assigner = {
        "city": lambda nav: nav["relevantHotelParams"]["localizedName"],
        "city_entityId": lambda nav: nav["relevantHotelParams"]["entityId"],
        "skyId": lambda nav: nav["relevantFlightParams"]["skyId"],
        "entityId": lambda nav: nav["relevantFlightParams"]["entityId"],
        "airport_name": lambda nav: nav["relevantFlightParams"]["localizedName"]
    }

    for key, function in result_dict_assigner.items():
        try:
            result_dict[key] = function(navigation)
        except:
            result_dict[key] = np.nan
    return result_dict

def get_country_airport_codes(response_data: list, country: str) -> list:
    """
    Filters and extracts airport codes from response data.
    
    Parameters:
    - response_data (list): List of dictionaries containing airport data.
    - country (str): The country name.
    
    Returns:
    - list: List of dictionaries with airport details.
    """
    airport_data_filtered = [d for d in response_data if d["navigation"]["entityType"] == "AIRPORT"]
    return [map_airport_codes(d, country) for d in airport_data_filtered]

def create_country_airport_code_df(list_of_countries: list) -> pd.DataFrame:
    """
    Fetches and creates a DataFrame of airport codes for given countries.
    
    Parameters:
    - list_of_countries (list): List of country names.
    
    Returns:
    - pd.DataFrame: DataFrame containing airport codes for the given countries.
    """
    list_of_countries_airports = []
    
    for country in list_of_countries:
        url = "https://sky-scrapper.p.rapidapi.com/api/v1/flights/searchAirport"
        querystring = {"query": country, "locale": "en-US"}
        headers = {
            "x-rapidapi-key": AIR_SCRAPPER_API_KEY,
            "x-rapidapi-host": "sky-scrapper.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers, params=querystring)
        response_data = response.json()["data"]
        list_of_countries_airports.extend(get_country_airport_codes(response_data, country))

    return pd.DataFrame(list_of_countries_airports)

def extract_flight_info_aller_retour(flight_dict: dict) -> dict:
    """
    Extracts detailed flight information from a flight dictionary.
    
    Parameters:
    - flight_dict (dict): Dictionary containing flight details.
    
    Returns:
    - dict: Dictionary with extracted flight information.
    """
    flight_result_dict = {}

    flight_result_dict_assigner = {
        'score': lambda flight: float(flight['score']),
        'price': lambda flight: int(flight['price']['formatted'].split()[0].replace(",", "")),
        'price_currency': lambda flight: flight['price']['formatted'].split()[1],
        'duration_departure': lambda flight: int(flight['legs'][0]['durationInMinutes']),
        'duration_return': lambda flight: int(flight['legs'][1]['durationInMinutes']),
        'stops_departure': lambda flight: int(flight['legs'][0]['stopCount']),
        'stops_return': lambda flight: int(flight['legs'][1]['stopCount']),
        'departure_departure': lambda flight: pd.to_datetime(flight['legs'][0]['departure']),
        'arrival_departure': lambda flight: pd.to_datetime(flight['legs'][0]['arrival']),
        'departure_return': lambda flight: pd.to_datetime(flight['legs'][1]['departure']),
        'arrival_return': lambda flight: pd.to_datetime(flight['legs'][1]['arrival']),
        'company_departure': lambda flight: flight['legs'][0]['carriers']['marketing'][0]['name'],
        'company_return': lambda flight: flight['legs'][1]['carriers']['marketing'][0]['name'],
        'self_transfer': lambda flight: flight['isSelfTransfer'],
        'fare_isChangeAllowed': lambda flight: flight['farePolicy']['isChangeAllowed'],
        'fare_isPartiallyChangeable': lambda flight: flight['farePolicy']['isPartiallyChangeable'],
        'fare_isCancellationAllowed': lambda flight: flight['farePolicy']['isCancellationAllowed'],
        'fare_isPartiallyRefundable': lambda flight: flight['farePolicy']['isPartiallyRefundable'],
        'origin_airport_departure': lambda flight: flight['legs'][0]['origin']['name'],
        'destination_airport_departure': lambda flight: flight['legs'][0]['destination']['name'],
        'origin_airport_return': lambda flight: flight['legs'][1]['origin']['name'],
        'destination_airport_return': lambda flight: flight['legs'][1]['destination']['name']
    }

    for key, function in flight_result_dict_assigner.items():
        try:
            flight_result_dict[key] = function(flight_dict)
        except KeyError:
            flight_result_dict[key] = np.nan  

    return flight_result_dict

def request_flight_itineraries_aller_retour(countries_airports_df: pd.DataFrame, origin_city: str, 
                                            destination_city: str, date_departure: str, date_return: str, 
                                            n_adults: int = 1, n_children: int = 0, n_infants: int = 0, 
                                            origin_airport_code: str = None, destination_airport_code: str = None, 
                                            cabin_class: str = "economy", sort_by: str = "best", currency: str = "EUR") -> list:
    """
    Requests flight itineraries between two cities, round-trip.
    
    Parameters:
    - countries_airports_df (pd.DataFrame): DataFrame of airport codes.
    - origin_city (str): Origin city.
    - destination_city (str): Destination city.
    - date_departure (str): Departure date.
    - date_return (str): Return date.
    - n_adults (int): Number of adults.
    - n_children (int): Number of children.
    - n_infants (int): Number of infants.
    - origin_airport_code (str): Origin airport code.
    - destination_airport_code (str): Destination airport code.
    - cabin_class (str): Cabin class (economy, business, etc.).
    - sort_by (str): Sorting criterion (best, cheapest, fastest, etc.).
    - currency (str): Currency for the price.
    
    Returns:
    - list: List of flight itineraries.
    """
    url = "https://sky-scrapper.p.rapidapi.com/api/v2/flights/searchFlightsComplete"
    cabin_class_list = ["economy", "premium_economy", "business", "first"]
    cabin_class = cabin_class if cabin_class in cabin_class_list else "economy"

    try:
        origin_city_id = str(int(countries_airports_df.loc[countries_airports_df["city"].str.lower() == origin_city.lower(), "city_entityId"].iloc[0]))
    except:
        pass
    try:
        destination_city_id = str(int(countries_airports_df.loc[countries_airports_df["city"].str.lower() == destination_city.lower(), "city_entityId"].iloc[0]))
    except:
        pass
    
    querystring = {
        "originSkyId": origin_city,
        "destinationSkyId": destination_city,
        "originEntityId": origin_city_id,
        "destinationEntityId": destination_city_id,
        "date": date_departure,
        "returnDate": date_return,
        "cabinClass": cabin_class,
        "adults": str(n_adults),
        "childrens": str(n_children),
        "infants": str(n_infants),
        "sortBy": sort_by,
        "currency": currency
    }

    headers = {
        "x-rapidapi-key": AIR_SCRAPPER_API_KEY,
        "x-rapidapi-host": "sky-scrapper.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    if response.status_code == 200:
        try:
            return response.json()["data"]["itineraries"]
        except:
            return np.nan
    else:
        raise ValueError("Failed to retrieve itineraries")

def create_itineraries_dataframe_aller_retour(itineraries_dict_list: list) -> pd.DataFrame:
    """
    Creates a DataFrame from a list of itineraries.
    
    Parameters:
    - itineraries_dict_list (list): List of flight itinerary dictionaries.
    
    Returns:
    - pd.DataFrame: DataFrame of flight itineraries.
    """
    extracted_itinerary_info_list = [extract_flight_info_aller_retour(itinerary) for itinerary in itineraries_dict_list]
    return pd.DataFrame(extracted_itinerary_info_list)

def extract_flight_info(flight_dict: dict) -> dict:
    """
    Extracts flight information from a flight dictionary (one-way).
    
    Parameters:
    - flight_dict (dict): Dictionary containing flight details.
    
    Returns:
    - dict: Dictionary with extracted flight information.
    """
    flight_result_dict = {}

    flight_result_dict_assigner = {
        'duration': lambda flight: int(flight['legs'][0]['durationInMinutes']),
        'price': lambda flight: int(flight['price']['formatted'].split()[0].replace(",", "")),
        'price_currency': lambda flight: flight['price']['formatted'].split()[1],
        'stops': lambda flight: int(flight['legs'][0]['stopCount']),
        'departure': lambda flight: pd.to_datetime(flight['legs'][0]['departure']),
        'arrival': lambda flight: pd.to_datetime(flight['legs'][0]['arrival']),
        'company': lambda flight: flight['legs'][0]['carriers']['marketing'][0]['name'],
        'self_transfer': lambda flight: flight['isSelfTransfer'],
        'fare_isChangeAllowed': lambda flight: flight['farePolicy']['isChangeAllowed'],
        'fare_isPartiallyChangeable': lambda flight: flight['farePolicy']['isPartiallyChangeable'],
        'fare_isCancellationAllowed': lambda flight: flight['farePolicy']['isCancellationAllowed'],
        'fare_isPartiallyRefundable': lambda flight: flight['farePolicy']['isPartiallyRefundable'],
        'score': lambda flight: float(flight['score']),
        'origin_airport': lambda flight: flight['legs'][0]['origin']['name'],
        'destination_airport': lambda flight: flight['legs'][0]['destination']['name']
    }

    for key, function in flight_result_dict_assigner.items():
        try:
            flight_result_dict[key] = function(flight_dict)
        except KeyError:
            flight_result_dict[key] = np.nan  

    return flight_result_dict

def request_flight_itineraries(countries_airports_df: pd.DataFrame, origin_city: str, 
                               destination_city: str, date: str, n_adults: int = 1, 
                               n_children: int = 0, n_infants: int = 0, origin_airport_code: str = None, 
                               destination_airport_code: str = None, cabin_class: str = "economy", 
                               sort_by: str = "best", currency: str = "EUR") -> list:
    """
    Requests flight itineraries for one-way flights.
    
    Parameters:
    - countries_airports_df (pd.DataFrame): DataFrame of airport codes.
    - origin_city (str): Origin city.
    - destination_city (str): Destination city.
    - date (str): Flight date.
    - n_adults (int): Number of adults.
    - n_children (int): Number of children.
    - n_infants (int): Number of infants.
    - origin_airport_code (str): Origin airport code.
    - destination_airport_code (str): Destination airport code.
    - cabin_class (str): Cabin class (economy, business, etc.).
    - sort_by (str): Sorting criterion (best, cheapest, fastest, etc.).
    - currency (str): Currency for the price.
    
    Returns:
    - list: List of flight itineraries.
    """
    url = "https://sky-scrapper.p.rapidapi.com/api/v2/flights/searchFlightsComplete"
    cabin_class_list = ["economy", "premium_economy", "business", "first"]
    cabin_class = cabin_class if cabin_class in cabin_class_list else "economy"

    try:
        origin_city_id = str(int(countries_airports_df.loc[countries_airports_df["city"].str.lower() == origin_city.lower(), "city_entityId"].iloc[0]))
    except:
        pass
    try:
        destination_city_id = str(int(countries_airports_df.loc[countries_airports_df["city"].str.lower() == destination_city.lower(), "city_entityId"].iloc[0]))
    except:
        pass

    querystring = {
        "originSkyId": origin_city,
        "destinationSkyId": destination_city,
        "originEntityId": origin_city_id,
        "destinationEntityId": destination_city_id,
        "date": date,
        "cabinClass": cabin_class,
        "adults": str(n_adults),
        "childrens": str(n_children),
        "infants": str(n_infants),
        "sortBy": sort_by,
        "currency": currency
    }

    headers = {
        "x-rapidapi-key": AIR_SCRAPPER_API_KEY,
        "x-rapidapi-host": "sky-scrapper.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    if response.status_code == 200:
        try:
            return response.json()["data"]["itineraries"]
        except:
            return np.nan
    else:
        raise ValueError("Failed to retrieve itineraries")

def create_itineraries_dataframe(itineraries_dict_list: list) -> pd.DataFrame:
    """
    Creates a DataFrame from a list of one-way flight itineraries.
    
    Parameters:
    - itineraries_dict_list (list): List of flight itinerary dictionaries.
    
    Returns:
    - pd.DataFrame: DataFrame of flight itineraries.
    """
    extracted_itinerary_info_list = [extract_flight_info(itinerary) for itinerary in itineraries_dict_list]
    return pd.DataFrame(extracted_itinerary_info_list)
