# xml_to_json.py
import xmltodict
import json
import sys
import os

JSON_DESTINATION = 'json_maps'


def convert(file_name): 
    '''Creates a json file from an xml file and returns the name'''
    with open(file_name) as xml_file:
        data_dict = xmltodict.parse(xml_file.read())
        
    json_data = json.dumps(data_dict, indent=" ")
    
    base_name = os.path.basename(file_name)
    json_file_name = f"{os.path.splitext(base_name)[0]}_data.json"
    output_file_path = os.path.join(JSON_DESTINATION, json_file_name)
    
    print(f"Creating json file at: {output_file_path}")
    with open(output_file_path, "w") as json_file:
        json_file.write(json_data)
        
    return json_file_name
        
    
if __name__ == "__main__":
    if len(sys.argv) == 2:
        print(f"Converting {sys.argv[1]}")
        convert(sys.argv[1])
        print("Done")
    else:
        print("No conversion done")