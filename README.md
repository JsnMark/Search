**How to use**
1) Go to https://www.openstreetmap.org/ and export a map. The map will be in xml which can be converted to json by running xml_to_json.py. Run the file with your OSM xml file as a command line argument.
2) Run search.py with the json file as a command line argument and follow the directions given by the standard output.
3) You should now see a file called osm_path.html which when opened using a browser, contains a map with a blue path between the two locations.

**Limitations**

Your beginning and end locations must be within the map, and there must be a path between the two locations bounded by the map.
Maps are manually exported instead of directly using the OSM api since the program may make too many or too large requests. 
Map data is limited by OSM. Since OSM gets its data from volunteers, information may not be 100% accurate or up to date. For example, gated roads into residential communities may be considered for pathfinding since they are not marked on OSM.

**Required Packages**
- geopy
- folium
