# search_geocoder.py
from geopy.geocoders import Nominatim


class AddressNotFound(Exception):
    pass

def address_to_coordinates(address: str) -> tuple:
    '''Converts a string address to coordinates. If the address does not work, raise exception'''
    
    geolocator = Nominatim(user_agent="jsm_search_geocoder")
    location = geolocator.geocode(address)
    if not location:
        raise AddressNotFound
    return location.latitude, location.longitude
    