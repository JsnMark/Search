# test_search_geocoder.py
import unittest
from search_geocoder import *

class GeocodeTest(unittest.TestCase):
    def setUp(self):
        self.working_address = "175 5th Avenue NYC"
        self.non_working_address = "10000000000000 5th Avenue NYC"
        
    def test_creates_location(self):
        location = address_to_coordinates(self.working_address)
        self.assertTrue(location)
        self.assertTrue(type(location)==tuple)
        self.assertTrue(len(location)==2)
        self.assertTrue(type(location[0])==float)
        self.assertTrue(type(location[1])==float)
        
    def test_does_not_make_incorrect_location(self):
        with self.assertRaises(AddressNotFound):
            location = address_to_coordinates(self.non_working_address)
        
if __name__ == "__main__":
    unittest.main()