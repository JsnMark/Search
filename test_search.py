# test_search.py
from search import *
import unittest
import json
import os
import random

# USE THIS FILE TO TEST 
# THERE IS A PATH FROM CVS PHARMACY TO MARK JUPITER
# CVS:          79 Jay St, Brooklyn, NY 11201
# Mark Jupiter: 191 Plymouth St, Brooklyn, NY 11201
TEST_JSON_FILE = "json_maps/nymap3_data.json"

MOCK_JSON_DATA = {
    "osm": {
        "bounds": {
            "@minlat": "40",
            "@minlon": "-120",
            "@maxlat": "50",
            "@maxlon": "-100"
         },
        "node": [
            {
                "@id": "12345",
                "@lat": "45.5",
                "@lon": "-100.5"   
            },
            {
                "@id": "54321",
                "@lat": "47",
                "@lon": "-110"   
            },
            {
                "@id": "11111",
                "@lat": "45.4999",
                "@lon": "-100.5"   
            }
        ],
        "way": [
            {
                "@id": "100",
                "nd": [
                    {
                        "@ref": "12345"
                    },
                    {
                        "@ref": "11111"
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
        self.node = OSMNode(osm_id=12345, lat=120.5, lon=45.575)
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
        new_node = OSMNode(self.node.id, self.node.coordinate.lat, self.node.coordinate.lon)
        self.assertTrue(new_node == self.node)
        
        new_node_1 = OSMNode(3, self.node.coordinate.lat, self.node.coordinate.lon)
        self.assertFalse(new_node_1 == self.node)
        
        new_node_1 = OSMNode(self.node.id, 3, self.node.coordinate.lon)
        self.assertFalse(new_node_1 == self.node)
        
        new_node_1 = OSMNode(self.node.id, self.node.coordinate.lat, 3)
        self.assertFalse(new_node_1 == self.node)

class WayTest(unittest.TestCase):
    def setUp(self):
        self.node = OSMNode(osm_id=12345, lat=120.5, lon=45.575)
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

class SearchTestUsingMockData(unittest.TestCase):
    def setUp(self):
        self.mapdict = MOCK_JSON_DATA
        self.waydict = create_way_dict(self.mapdict)
        self.nodedict = create_node_dict(self.mapdict)
        self.bbox = get_bounding_box(self.mapdict)
        
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
        
        self.assertTrue(len(node_dict)==3)
        self.assertTrue(node_dict[12345].id == 12345)
        self.assertTrue(node_dict[12345].coordinate.lat == 45.5)
        
    def test_correctly_creates_way_dict(self):
        way_dict = create_way_dict(MOCK_JSON_DATA)
        
        self.assertTrue(len(way_dict)==2)
        self.assertTrue(way_dict[100].id == 100)
        self.assertTrue(way_dict[100].highway_value == "tertiary")
        
        self.assertTrue(way_dict[101].id == 101)
        self.assertTrue(way_dict[101].highway_value == None)

    def test_gets_correct_tailnodes_given_node_ids(self):
        beg = get_node_from_id(self.mapdict, self.nodedict, 12345)
        end = get_node_from_id(self.mapdict, self.nodedict, 54321)
        self.assertTrue(type(beg) == OSMNode)
        self.assertEqual(beg.id, 12345)
        self.assertEqual(beg.coordinate, Point(45.5, -100.5))
        
        self.assertTrue(type(end) == OSMNode)
        self.assertEqual(end.id, 54321)
        self.assertEqual(end.coordinate, Point(47.0, -110.0))
        
    def test_creates_correct_bbox(self):
        bbox = get_bounding_box(self.mapdict)
        self.assertTrue(bbox.minlat == 40)
        self.assertTrue(bbox.minlon == -120)
        self.assertTrue(bbox.maxlat == 50)
        self.assertTrue(bbox.maxlon == -100)
        
    def test_haversine_distance_is_same_for_differnt_order(self):
        p1 = Point(51.510357, -0.116773)
        p2 = Point(38.889931, -77.009003)
        self.assertAlmostEqual(5897.658, round(haversine(p1, p2), 3))
        self.assertAlmostEqual(5897.658, round(haversine(p2, p1), 3))
        
    def test_heuristic(self):
        p1 = Point(51.510357, -0.116773)
        p2 = Point(38.889931, -77.009003)
        n1 = OSMNode(1, p1.lat, p1.lon)
        n2 = OSMNode(2, p2.lat, p2.lon)
        self.assertAlmostEqual(5897.658, round(heuristic(n1, n2), 3))
        self.assertAlmostEqual(5897.658, round(heuristic(n2, n1), 3))
        
    def test_add_ways_to_nodes(self):
        add_all_ways_to_nodes(self.waydict, self.nodedict)
        self.assertEqual(self.nodedict[12345].ways, {100})
        self.assertEqual(self.nodedict[54321].ways, {101})
        
    def test_coordinates_to_nodes(self):
        add_all_ways_to_nodes(self.waydict, self.nodedict)
        p = Point(45.5001, -100.5)
        ls = coordinates_to_nodes(p, self.nodedict, self.waydict, self.bbox)
        self.assertEqual(len(ls), 1)
        self.assertEqual(type(ls[0]), OSMNode)
        self.assertEqual(ls[0].id, 12345)
    
    def test_c2n_does_not_add_far_nodes(self):
        add_all_ways_to_nodes(self.waydict, self.nodedict)
        p = Point(45.6, -100.5)
        ls = coordinates_to_nodes(p, self.nodedict, self.waydict, self.bbox)
        self.assertTrue(all(x == None for x in ls))
        
class AnodeAndFrontierTestUsingTestJsonFile(unittest.TestCase):
    def setUp(self):
        self.mapdict = load_json_to_dict(TEST_JSON_FILE)
        self.waydict = create_way_dict(self.mapdict)
        self.nodedict = create_node_dict(self.mapdict)
        self.bbox = get_bounding_box(self.mapdict)
        add_all_ways_to_nodes(self.waydict, self.nodedict)
        
        self.map = Map(self.nodedict, self.waydict, self.bbox)
        
        node_id, osm_node = random.choice(list(self.nodedict.items()))
        node = AstarNode(osm_node, 0, 100, None)
        self.nodedict.pop(node_id)
        self.f = Frontier(node)
    
    def test_astar_nodes_can_be_created_from_osm_nodes(self):
        node_id, osm_node = random.choice(list(self.nodedict.items()))
        anode = AstarNode(osm_node, 2, 1.1, None)
        self.assertTrue(anode.OSM_node == osm_node)
        self.assertTrue(anode.gcost == 2)
        self.assertTrue(anode.hcost == 1.1)
        self.assertTrue(anode.pathcost == 3.1)
        self.assertTrue(anode.parent is None)
    
    def test_astar_node_contains_parent(self):
        node_id, osm_node = random.choice(list(self.nodedict.items()))
        self.nodedict.pop(node_id)
        parent_id, parent_node = random.choice(list(self.nodedict.items()))
        
        parent = AstarNode(parent_node, 4, 5, None)
        anode = AstarNode(osm_node, 2, 1.1, parent)
        
        self.assertTrue(anode.parent == parent)
        self.assertTrue(type(anode.parent)==AstarNode)
        self.assertTrue(parent.parent == None)
    
    def test_setup_frontier(self):
        node_id, osm_node = random.choice(list(self.nodedict.items()))
        node = AstarNode(osm_node, 0, 100, None)
        self.nodedict.pop(node_id)
        f = Frontier(node)
        
        self.assertTrue(len(f.deque) == 1)
        self.assertTrue(node in f.deque)
        
        
    def test_remove_from_frontier(self):
        self.f.remove()
        self.assertTrue(len(self.f.deque) == 0)
        # error when removing from empty deque
        with self.assertRaises(IndexError):
            self.f.remove()
            
    def test_frontier_is_empty(self):
        self.assertFalse(self.f.is_empty())
        self.assertTrue(len(self.f.deque) == 1)
        self.f.remove()
        self.assertTrue(self.f.is_empty())
        self.assertTrue(len(self.f.deque) == 0)
        
    def test_add_to_end_of_frontier(self):
        ls = list(self.nodedict.values())
        anode1 = AstarNode(random.choice(ls), 1, 100, None)
        anode2 = AstarNode(random.choice(ls), 30, 75, anode1)
        
        f = Frontier(anode1)
        f.add(anode2)
        
        self.assertTrue(len(f.deque) == 2)
        self.assertTrue(f.deque[0] == anode1)
        self.assertTrue(f.deque[1] == anode2)
    
    def test_add_to_front_of_frontier(self):
        ls = list(self.nodedict.values())
        anode1 = AstarNode(random.choice(ls), 1, 100, None)
        anode2 = AstarNode(random.choice(ls), 30, 75, anode1)
        
        f = Frontier(anode1)
        f.add(anode2)
        
        anode0 = AstarNode(random.choice(ls), 0, 80, anode1)
        f.add(anode0)
        self.assertTrue(len(f.deque) == 3)
        self.assertTrue(f.deque[0] == anode0)
        self.assertTrue(f.deque[1] == anode1)
        self.assertTrue(f.deque[2] == anode2)
        
    def test_add_to_middle_of_frontier(self):
        ls = list(self.nodedict.values())
        anode1 = AstarNode(random.choice(ls), 1, 100, None)
        anode3 = AstarNode(random.choice(ls), 30, 75, anode1)
        f = Frontier(anode1)
        f.add(anode3)
        anode0 = AstarNode(random.choice(ls), 0, 80, anode1)
        f.add(anode0)
        
        anode2 = AstarNode(random.choice(ls), 40, 62, anode3)
        
class MapTestUsingJsonFile(unittest.TestCase):
    def setUp(self):
        self.mapdict = load_json_to_dict(TEST_JSON_FILE)
        self.waydict = create_way_dict(self.mapdict)
        self.nodedict = create_node_dict(self.mapdict)
        self.bbox = get_bounding_box(self.mapdict)
        add_all_ways_to_nodes(self.waydict, self.nodedict)
        
        self.map = Map(self.nodedict, self.waydict, self.bbox)
        
        # closest street node to CVS
        self.start_osm_node = self.nodedict[9805235577]
        # closest street node to Mark Jupiter
        self.goal_osm_node = self.nodedict[7707712198]
        
        self.start_anode = AstarNode(self.start_osm_node, 0, heuristic(self.start_osm_node, self.goal_osm_node), None)
        self.frontier = Frontier(self.start_anode)
    
    def test_finds_all_neighbors(self):
        # All neighbors to 9805235577, found by hand
        self.map.osm_goal = self.goal_osm_node
        start_neighbors = set([42497720, 10722370766, 10722370765, 7707712197])
        n = self.map.neighbors(self.start_anode)
        n = set([x.OSM_node.id for x in n])
        self.assertEqual(n, start_neighbors)

        end_neighbors = set([42472725, 3000082229, 3000084335, 7707712199, 10725896470, 2358967531])
        n = self.map.neighbors(AstarNode(self.goal_osm_node, 0, 0, None))
        n = set([x.OSM_node.id for x in n])
        self.assertEqual(n, end_neighbors)

    def test_expanding_with_neighbors(self):
        self.map.osm_goal = self.goal_osm_node
        start_neighbors = self.map.neighbors(self.start_anode)
        
        self.map.expand(self.frontier, start_neighbors)
        
        costs = [x.pathcost for x in self.frontier.deque]
        # Ascending pathcost order
        for i in range(len(costs)-1):
            self.assertTrue(costs[i] < costs[i + 1])
        
        
if __name__ == '__main__':
    unittest.main()