# search.py 

import sys
import urllib.request
import urllib.parse
import json
import search_geocoder
import math
from collections import namedtuple
from collections import deque
import folium_test

# Overpass API is not used since it may exceed limit. 
#   Instead, map data is downloaded from OSM

HIGHWAY_VALUES = ["motorway", "trunk", "primary", "secondary", "tertiary", "unclassified", "residential",
                  "motorway_link", "trunk_link", "primary_link", "secondary_link", "tertiary_link",
                  "living_street", "service", "road"]

AMOUNT_OF_CLOSEST_NODES = 5

# (In km)
MAX_DISTANCE_BETWEEN_NODES = 0.13

Point = namedtuple('Point', ['lat', 'lon'])

class OSMNode:
    def __init__(self, osm_id: int, lat: float, lon: float):
        self.id = osm_id
        self.coordinate = Point(lat, lon)
        self.ways = set()
        
    def __eq__(self, other):
        '''Memberwise equality'''
        if type(other) is OSMNode:
            return self.id == other.id \
                and self.coordinate == other.coordinate \
                and self.ways == other.ways
        else:
            return NotImplemented
    
    def add_way(self, way: int):
        '''Adds the way id to the set of the node's ways it belongs to'''
        self.ways.add(way)
             
class Way:
    def __init__(self, osm_id: int):
        self.id = osm_id
        self.nodes = set()
        self.highway_value = None
    
    def add_node(self, node: int):
        self.nodes.add(node)

class BoundingBox:
    def __init__(self, minlat, minlon, maxlat, maxlon):
        if minlat > maxlat or minlon > maxlon:
            raise Exception("Boundingbox has incorrect boundaries")
        
        self.minlat = minlat
        self.minlon = minlon
        self.maxlat = maxlat
        self.maxlon = maxlon
        
    def __repr__(self):
        return f"minlat: {self.minlat}, minlon: {self.minlon}, maxlat: {self.maxlat}, maxlon: {self.maxlon}"
        
    def check_inside(self, point: Point) -> bool:
        '''returns true if the coordinates given is inside the bbox, false otherwise.'''
        return self.minlat <= point.lat and self.minlon <= point.lon and self.maxlat >= point.lat and self.maxlon >= point.lon

class AstarNode():
    def __init__(self, OSM_node: OSMNode, gcost: float, hcost:float, parent: 'Astar_Node or None'):
        # gcost (cost to reach node)
        # hcost (estimated cost to goal)
        self.OSM_node = OSM_node
        self.gcost = gcost
        self.hcost = hcost
        self.pathcost = gcost + hcost
        self.parent = parent

class Frontier():
    def __init__(self, initial_node: AstarNode):
        self.deque = deque([initial_node])
        
    def is_empty(self):
        '''returns if frontier is empty'''
        return not bool(len(self.deque))
    
    def remove(self):
        '''removes and returns left most (least pathcost) node in frontier'''
        return self.deque.popleft()

    def add(self, anode):
        '''adds an anode given its pathcost'''
        
        # search for its position, add the anode at that position
        low = 0
        high = len(self.deque) - 1
        mid = 0
        
        while low <= high:
            mid = (low + high) // 2
            if anode.pathcost == self.deque[mid].pathcost:
                self.deque.insert(mid, anode)
                break
            
            if anode.pathcost > self.deque[mid].pathcost:
                low = mid + 1
            
            if anode.pathcost < self.deque[mid].pathcost:
                high = mid - 1
                
        if low > high:
            self.deque.insert(low, anode)

class Map():
    def __init__(self, node_dict, way_dict, bbox):
        self.node_dict = node_dict
        self.way_dict = way_dict
        self.bbox = bbox
        self.osm_goal = None
        
    def neighbors(self, anode):
        '''Returns a list of anodes to be added to the frontier'''
        node = anode.OSM_node
        ways = node.ways
        neighbor_results = []
        neighbor_ids = []
        # Append the actual traveled distance between the start node and its neighbors
        for way_id in ways:
            way = self.way_dict[way_id]
            # Checks if way is part of the highway value
            if way.highway_value != None:
                for node_id in way.nodes:
                    new_node = self.node_dict[node_id]
                    # If the node has not yet been reached or if it is the same node
                    if node_id not in neighbor_ids and node_id != node.id:
                        # gcost (cost to reach node)
                        gc = haversine(node.coordinate, new_node.coordinate)
                        # hcost (estimated cost to goal)
                        hc = haversine(self.osm_goal.coordinate, new_node.coordinate)
                        # Add the new anode to the list
                        neighbor_results.append(AstarNode(new_node, gc, hc, anode))
                        neighbor_ids.append(node_id)
        return neighbor_results 
    
    def expand(self, frontier, anodes, explored):
        '''expands the frontier given a list of anodes'''
        # If there are no more anodes, return
        if len(anodes) == 0:
            return
        
        # Get the first anode, add it in the right spot, remove it from the list
        current_anode = anodes.pop(0)
        if current_anode.OSM_node.id not in explored:
            frontier.add(current_anode)
        self.expand(frontier, anodes, explored)
        
        
    def search(self, start: OSMNode, goal: OSMNode):
        '''Tries to find a path from the start to the goal, if there is one, returns list of node ids if found'''
        self.osm_goal = goal
        beg_anode = AstarNode(start, 0, heuristic(start, goal), None)
        frontier = Frontier(beg_anode)
        explored = set()
        
        while True:
            # If frontier is empty, there is no solution
            if frontier.is_empty():
                print("Not found!")
                break
            # Pop the node at the very front of the frontier
            current_anode = frontier.remove()
            # If it is the goal node, we found a solution
            if current_anode.OSM_node == goal:
                # Create a list for the path we found
                path = []
                # Go back and add each nodes parents until we reach the starting node
                while current_anode.parent is not None:
                    path.append(current_anode.OSM_node)
                    current_anode = current_anode.parent
                # Add the start node
                path.append(current_anode.OSM_node)
                # Reverse this list so that our path is start to goal
                path.reverse()
                return path
            
            # since it is not the goal node, continue on by looking at its neighbors
            # Add the current node to the explored set
            explored.add(current_anode.OSM_node.id)
            # Now we have to add the next nodes to the frontier using our heuristic.
            neighbors_to_be_added = self.neighbors(current_anode)
            self.expand(frontier, neighbors_to_be_added, explored)
            




def ask_for_format() -> str:
    '''Gets the format of either nodes or addresses'''
    format = None
    while format == None:
        format = input("Enter 1 to use Nodes or 2 to use Addresses? ")
        if format == '1':
            return 'NODE' 
        elif format == '2':
            return 'ADDRESS'
        else:
            format = None
                       
def create_node_dict(map_dict: dict) -> dict:
    ''' Creates a node dict. format of map
    mapdict{
        osm{
            node{
                [
                    {}, {}, ...
                ]
            }
        }
    }
    '''
    node_dict = dict()
    
    # Add each node to the dict
    for item in map_dict["osm"]["node"]:
        new_node = OSMNode(osm_id=int(item['@id']), 
                        lat=float(item['@lat']), 
                        lon=float(item['@lon']))
        node_dict[int(item['@id'])] = new_node
    
    # If dict is empty, raise exception
    if node_dict == dict():
        raise Exception("Error: node_dict is empty")
    
    return node_dict

def create_way_dict(map_dict: dict) -> dict:
    '''Creates a dict for ways'''
    # "tag" will be dict if single entry of a dict, list if multiple entry of dicts
    
    way_dict = dict()
    for item in map_dict["osm"]["way"]:
        new_way = Way(osm_id=int(item['@id']))
        
        # Add the nodes that belong to the way
        for n in item["nd"]:
            new_way.add_node(int(n['@ref']))
        
        # Add the highway tag to the way
        if "tag" in item.keys(): 
            # If tag is a list
            if type(item["tag"]) == list:
                # Go through each unnamed dict
                for unnamed_entry in item["tag"]:
                    # if @k == highway
                    if unnamed_entry["@k"] == "highway":
                        # for each val, if it is a highway val, match it
                        for val in HIGHWAY_VALUES:
                            if unnamed_entry["@v"] == val:
                                new_way.highway_value = val
                                break
                    
            # If tag is a dict
            elif type(item["tag"] == dict):
                # If @k == highway
                if "@k" in item["tag"] and item["tag"]["@k"] == "highway":
                    # for each val, if it is a highway val, match it
                    for val in HIGHWAY_VALUES:
                        if item["tag"]["@v"] == val:
                            new_way.highway_value = val
                            break

        # Put the way into the dict
        way_dict[int(item['@id'])] = new_way
        
    # Check if dict is empty
    if way_dict == dict():
        raise Exception("Error: way_dict is empty")
    
    return way_dict

def add_all_ways_to_nodes(way_dict: dict, node_dict: dict) -> None:
    '''Takes in a way_dict and node_dict and assigns a node's way set if it is in a given way'''
    # For each node a part of every way
    for way_id in way_dict.keys():
        for node_id in way_dict[way_id].nodes:

            # If the node's id is in the node dictionary, update the node's way set
            if node_id in node_dict:
                node_dict[node_id].add_way(way_id)
           
def load_json_to_dict(map_file) -> dict:
    '''Loads json file of map to a dict. structure of dict:
        osm
            node[]
            way
            relation
    '''
    map_dict = None
    
    # Open file, load in data
    with open(map_file) as file:
        map_dict = json.load(file)
    if map_dict == None:
        raise Exception('Error: Map file contains nothing')
    return map_dict

def get_id_from_nodes(node_dict: dict) -> tuple:
    '''Gets the int ids from user'''
    try:
        # Get ids
        beg_id = int(input('Enter the start node id: '))
        end_id = int(input('Enter the end node id:   '))
        
        if beg_id not in node_dict or end_id not in node_dict:
            raise Exception("OSMNode Ids are not in the given node_dict")
        
        return beg_id, end_id
    # Bad user input
    except ValueError:
        sys.exit("Error: not a number")

def get_node_from_id(map_dict: dict, node_dict: dict, node_id) -> tuple:
    '''Get the beginning and end nodes given node ids'''

    # Check if nodes inside the node dict
    if node_id not in node_dict:
        raise Exception("Error: OSMNode id not found")
    
    return node_dict[node_id]

def get_bounding_box(map_dict: dict) -> BoundingBox:
    '''Gets the bounding box from the map_dict.'''
    # Takes data from the map_dict
    bounds = map_dict["osm"]["bounds"]
    minlat = float(bounds["@minlat"])
    minlon = float(bounds["@minlon"])
    maxlat = float(bounds["@maxlat"])
    maxlon = float(bounds["@maxlon"])
    
    # returns a BoundingBox
    return BoundingBox(minlat, minlon, maxlat, maxlon)
    
def haversine(p1: Point, p2: Point)->float:
    '''Calculates the haversine formula between 2 points and returns the distance in kilometers'''
    # https://en.wikipedia.org/wiki/Haversine_formula
    # https://community.esri.com/t5/coordinate-reference-systems-blog/distance-on-a-sphere-the-haversine-formula/ba-p/902128
    
    lat1 = p1.lat
    lon1 = p1.lon
    lat2 = p2.lat
    lon2 = p2.lon
    
    # Radius of earth in km
    radius = 6371
    
    # radian conversion
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    
    # deltas
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat / 2.0) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(delta_lon / 2.0) ** 2
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    km = c * radius
    return km
    
def coordinates_to_nodes(point: Point, node_dict: dict, way_dict: dict, bbox: BoundingBox) -> [OSMNode]:
    '''converts lat and lon coordinates to the nearest nodes (5 by default)'''
    
    # Check if within bounds
    if not bbox.check_inside(point):
        raise Exception(f"Coordinates({point.lat}, {point.lon}) are not within the given map's bounding box {bbox}")
    
    # Create an empty list of tuples the 5 closest nodes and their distance to the point 
    closest_nodes = [None for i in range(AMOUNT_OF_CLOSEST_NODES)]
    closest_distances = [math.inf for i in range(AMOUNT_OF_CLOSEST_NODES)]
    
    # (position of the max value, max value)
    max_pos = 0
    max_val = math.inf
    
    # look through all nodes and find node(s) closest that match the highway tags at the very top
    for node in node_dict.values():

        # If node not within specified meters, skip the node
        distance = haversine(point, node.coordinate)
        if distance > MAX_DISTANCE_BETWEEN_NODES:
            continue
        
        # If the distance farther than the max distnace in the list, skip the node
        if distance >= max_val:
            continue
        
        # If the node is not a part of a way with a specific highway value, skip the node
        if all(way_dict[w_id].highway_value == None for w_id in node.ways):    
            continue
        
        # Abnormal case
        # If the node belongs to a way, and another node in closest_list belongs to the same way,
        #   see which one is closer, add the closer one, but do not add nodes part of the same way
        
        # For each entry in the closest nodes list
        abnormal_case = False
        for i in range(AMOUNT_OF_CLOSEST_NODES):
            close_node = closest_nodes[i]
            
            # If it does not have a node, go to next entry
            if type(close_node) != OSMNode:
                continue
            
            # It has node, so check its ways
            close_node_ways = close_node.ways
            
            # For each of the found ways, if the way matches with the original node's ways, see which node is closer to the point
            for w in close_node_ways:
                if w in node.ways:
                    # Mark as abnormal case since they share a way
                    abnormal_case = True
                    distance_from_node_in_ls = haversine(point, close_node.coordinate)

                    # If the node in the list is closer, do nothing, else replace the node
                    if distance_from_node_in_ls > distance and node not in closest_nodes:
                        closest_nodes[i] = node
                        closest_distances[i] = distance
                
        # Normal case
        # Now we know we can add this node into our closest nodes list. Remove its max distance node for this node
        if not abnormal_case and node not in closest_nodes:
            closest_nodes[max_pos] = node
            closest_distances[max_pos] = distance
        
        # Find the new max_pos
        tmp_max_pos = None
        tmp_max_val = -math.inf
        
        # For each of the entrys in the closest nodes list
        for i in range(AMOUNT_OF_CLOSEST_NODES):
            # If its distance is greater than the tmp_max's, set the new position and distance of max_pos 
            if closest_distances[i] > tmp_max_val:
                tmp_max_pos = i
                tmp_max_val = closest_distances[i]
        
        # Change the maxes if they are found
        if tmp_max_pos != None and tmp_max_val != -math.inf:
            max_pos = tmp_max_pos
            max_val = tmp_max_val
        
    # Zip the distances and nodes, get rid of Nones, sort them by distances increasing
    zipped = zip(closest_distances, closest_nodes)
    zipped = [z for z in zipped if z[1] != None]
    sorted_closest_pairs = sorted(zipped)

    sorted_closest_nodes = [x[1] for x in sorted_closest_pairs]
    return sorted_closest_nodes
    
def get_id_from_geocoding_addresses(node_dict: dict, way_dict: dict, bbox: BoundingBox):
    '''Gets the node ids of the beginning and end points given addresses'''
    # Ask for addresses
    beg_add = input("Enter the start address: ")
    end_add = input("Enter the end address  : ")
    
    # Convert them to points
    beg_coord = Point(*search_geocoder.address_to_coordinates(beg_add))
    end_coord = Point(*search_geocoder.address_to_coordinates(end_add))
    
    # Convert cordinates to nodes
    beg_node_id_ls = [node.id for node in coordinates_to_nodes(beg_coord, node_dict, way_dict, bbox)]
    end_node_id_ls = [node.id for node in coordinates_to_nodes(end_coord, node_dict, way_dict, bbox)]

    return beg_node_id_ls, end_node_id_ls

def heuristic(node, goal_node):
    return haversine(node.coordinate, goal_node.coordinate)





def main():
    if len(sys.argv) != 2:
        raise Exception("No map found!")
    map_file = sys.argv[1]
    
    # Ask for the format of user input: nodes or addresses
    format_type = ask_for_format()
    
    # Load data into a dict
    print("Loading in the data (This may take a while depending on the size of the map)")
    map_dict = load_json_to_dict(map_file)
    
    # Make a node and way dictionary
    node_dict = create_node_dict(map_dict)
    way_dict = create_way_dict(map_dict)
    
    # Adds all ways to each node's way set in node_dict
    add_all_ways_to_nodes(way_dict, node_dict)
    
    # Make the bounding box
    bbox = get_bounding_box(map_dict)
    
    # Ask for beginning and end destinations
    beg, end = None, None
    beg_ids, end_ids = None, None
    if format_type == 'NODE':
        beg_id, end_id = get_id_from_nodes(node_dict)
    elif format_type == 'ADDRESS':
        beg_ids, end_ids = get_id_from_geocoding_addresses(node_dict, way_dict, bbox)
        beg_id = beg_ids[0]
        end_id = end_ids[0]
    
    # get nodes for the beginning and end
    print("Getting nodes")
    beg = get_node_from_id(map_dict, node_dict, beg_id)
    end = get_node_from_id(map_dict, node_dict, end_id)
    
    if beg == None or end == None:
        raise Exception("No beginning or end found")
    
    print("Solving")
    map_problem = Map(node_dict, way_dict, bbox)
    path = map_problem.search(beg,end)
    coord_ls = [(n.coordinate.lat, n.coordinate.lon) for n in path]

    folium_test.make_map(coord_ls)
        

if __name__ == "__main__":
    main()