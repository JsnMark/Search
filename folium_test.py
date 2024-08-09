import folium

def make_map(point_ls):
    start_node = point_ls[0]
    mymap = folium.Map(location=[start_node[0], start_node[1]], zoom_start=14)
    path = [(point[0], point[1]) for point in point_ls]
    folium.PolyLine(path, color="blue", weight=2.5, opacity=1).add_to(mymap)
    mymap.save("osm_path.html")
    print("Done")