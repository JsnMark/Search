# test_search.py
from search import *
import unittest
import json
import os


MOCK_JSON_DATA = {
    "osm": {
        "bounds": {
            "@minlat": "30",
            "@minlon": "-120",
            "@maxlat": "35",
            "@maxlon": "-115"
         },
        "node": [
            {
                "@id": "12345",
                "@lat": "120.5",
                "@lon": "45.575"   
            },
            {
                "@id": "54321",
                "@lat": "127",
                "@lon": "45.575"   
            }
        ],
        "way": [
            {
                "@id": "100",
                "nd": [
                    {
                        "@ref": "12345"
                    }
                ],
                "tag": [
                    {
                        "@k": "highway",
                        "@v": "tertiary"
                    }
                ]
            },
            {
                "@id": "101",
                "nd": [
                    {
                        "@ref": "54321"
                    }
                ],
                "tag": [
                    {
                        "@k": "highway",
                        "@v": "cycleway"
                    }
                ]                
            }
        ]
    }
}


class NodeTest(unittest.TestCase):
    def setUp(self):
        self.node = Node(osm_id=12345, lat=120.5, lon=45.575)
        self.way = Way(100)
        
    def test_nodes_have_correct_data(self):
        self.assertTrue(self.node.id==12345)
        self.assertTrue(self.node.coordinate==Point(120.5, 45.575))
        
    def test_nodes_have_no_ways_on_construction(self):
        self.assertEqual(self.node.ways, set())
        
    def test_nodes_can_add_ways(self):
        self.node.add_way(self.way.id)
        self.assertEqual(set, type(self.node.ways))
        self.assertEqual(self.node.ways, {100})
        self.assertEqual(len(self.node.ways), 1)
        
    def test_cannot_add_same_way_multiple_times(self):
        self.node.add_way(self.way.id)
        self.node.add_way(self.way.id)
        
        self.assertEqual(len(self.node.ways), 1)
        
    def test_node__eq__(self):
        new_node = Node(self.node.id, self.node.coordinate.lat, self.node.coordinate.lon)
        self.assertTrue(new_node == self.node)
        
        new_node_1 = Node(3, self.node.coordinate.lat, self.node.coordinate.lon)
        self.assertFalse(new_node_1 == self.node)
        
        new_node_1 = Node(self.node.id, 3, self.node.coordinate.lon)
        self.assertFalse(new_node_1 == self.node)
        
        new_node_1 = Node(self.node.id, self.node.coordinate.lat, 3)
        self.assertFalse(new_node_1 == self.node)


class WayTest(unittest.TestCase):
    def setUp(self):
        self.node = Node(osm_id=12345, lat=120.5, lon=45.575)
        self.way = Way(100)
        
    def test_ways_have_correct_data(self):
        self.assertTrue(self.way.id==100)
        self.assertTrue(self.way.nodes==set())
        
    def test_ways_have_no_nodes_on_construction(self):
        self.assertEqual(self.way.nodes, set())
        
    def test_ways_can_add_nodes(self):
        self.way.add_node(self.node.id)
        self.assertEqual(set, type(self.way.nodes))
        self.assertEqual(self.way.nodes, {12345})
        self.assertEqual(len(self.way.nodes), 1)
        
    def test_cannot_add_same_node_multiple_times(self):
        self.way.add_node(self.node.id)
        self.way.add_node(self.node.id)
        self.assertEqual(len(self.way.nodes), 1)
        

class BoundingBoxTest(unittest.TestCase):
    def test_create_bbox(self):
        bbox = BoundingBox(120.5, 125.5, 126, 125.6)
        self.assertTrue(bbox.minlat <= bbox.maxlat)
        self.assertTrue(bbox.minlon <= bbox.maxlon)
        
        self.assertTrue(bbox.minlat == 120.5)
        self.assertTrue(bbox.minlon == 125.5)
        self.assertTrue(bbox.maxlat == 126)
        self.assertTrue(bbox.maxlon == 125.6)
        
    def test_raises_error_on_incorrect_boundaries(self):
        with self.assertRaises(Exception):
            bbox = BoundingBox(10, 10, 5, 15)
        with self.assertRaises(Exception):
            bbox = BoundingBox(10, 10, 15, 5)
    
    def test_can_tell_if_given_coordinates_are_inside_bbox(self):
        bbox = BoundingBox(0, 0, 100, 100)
        self.assertTrue(bbox.check_inside(Point(50, 50)))
        self.assertFalse(bbox.check_inside(Point(50, 160)))
        self.assertFalse(bbox.check_inside(Point(160, 50)))
        self.assertFalse(bbox.check_inside(Point(-100, 50)))
        self.assertFalse(bbox.check_inside(Point(50, -100)))
        self.assertFalse(bbox.check_inside(Point(-100, -100)))
        self.assertFalse(bbox.check_inside(Point(160, 160)))
        
        self.assertTrue(bbox.check_inside(Point(0, 50)))
        self.assertTrue(bbox.check_inside(Point(50, 100)))

class SearchTest(unittest.TestCase):
    def setUp(self):
        self.mapdict = MOCK_JSON_DATA
        self.waydict = create_way_dict(self.mapdict)
        self.nodedict = create_node_dict(self.mapdict)
        
    def test_loads_data_into_dict(self):
        with open("tmp.json", "w") as tmp:
            json.dump(MOCK_JSON_DATA, tmp)
            
        json_dict = load_json_to_dict("tmp.json")
        self.assertTrue(json_dict == MOCK_JSON_DATA)
            
        if os.path.exists("tmp.json"):
            os.remove("tmp.json")
        else:
            raise Exception("Could not delete tmp.json since it does not exist") 
 
    def test_correctly_creates_node_dict(self):
        node_dict = create_node_dict(MOCK_JSON_DATA)
        
        self.assertTrue(len(node_dict)==2)
        self.assertTrue(node_dict[12345].id == 12345)
        self.assertTrue(node_dict[12345].coordinate.lat == 120.5)
        
    def test_correctly_creates_way_dict(self):
        way_dict = create_way_dict(MOCK_JSON_DATA)
        
        self.assertTrue(len(way_dict)==2)
        self.assertTrue(way_dict[100].id == 100)
        self.assertTrue(way_dict[100].highway_value == "tertiary")
        
        self.assertTrue(way_dict[101].id == 101)
        self.assertTrue(way_dict[101].highway_value == None)

    def test_gets_correct_tailnodes_given_node_ids(self):
        beg, end = get_tails_from_nodes(self.mapdict, self.nodedict, 12345, 54321)
        self.assertTrue(type(beg) == Node)
        self.assertEqual(beg.id, 12345)
        self.assertEqual(beg.coordinate, Point(120.5, 45.575))
        
        self.assertTrue(type(end) == Node)
        self.assertEqual(end.id, 54321)
        self.assertEqual(end.coordinate, Point(127, 45.575))
        
    def test_creates_correct_bbox(self):
        bbox = get_bounding_box(self.mapdict)
        self.assertTrue(bbox.minlat == 30)
        self.assertTrue(bbox.minlon == -120)
        self.assertTrue(bbox.maxlat == 35)
        self.assertTrue(bbox.maxlon == -115)
        
    def test_haversine_distance_is_same_for_differnt_order(self):
        p1 = Point(51.510357, -0.116773)
        p2 = Point(38.889931, -77.009003)
        self.assertAlmostEqual(5897.658, round(haversine(p1, p2), 3))
        self.assertAlmostEqual(5897.658, round(haversine(p2, p1), 3))
        
    def test_add_ways_to_nodes(self):
        add_all_ways_to_nodes(self.waydict, self.nodedict)
        self.assertEqual(self.nodedict[12345].ways, {100})
        self.assertEqual(self.nodedict[54321].ways, {101})
        
        
if __name__ == '__main__':
    unittest.main()