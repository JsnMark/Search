import folium

def make_map(point_ls):
    # make a map with the start node
    start_node = point_ls[0]
    mymap = folium.Map(location=[start_node[0], start_node[1]], zoom_start=14)
    
    # add the path to the map
    path = [(point[0], point[1]) for point in point_ls]
    folium.PolyLine(path, color="blue", weight=2.5, opacity=1).add_to(mymap)
    
    # Add each point as a marker
    for point in point_ls:
        folium.Marker([point[0], point[1]]).add_to(mymap)
        
    # Save the map
    mymap.save("osm_path.html")
    print("Done")