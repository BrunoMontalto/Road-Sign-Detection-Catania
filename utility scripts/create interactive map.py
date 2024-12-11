import os
import folium
import xml.etree.ElementTree as ET

def extract_coordinates_and_ids(file_path):
    data = []
    
    try:
        # parse the XML file
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # iterate through entries and extract id, latitude, and longitude
        for entry in root.findall(".//entry"):  # Adjust path if needed
            entry_id = entry.get('id')
            latitude = entry.find('latitude').text
            longitude = entry.find('longitude').text
            
            # convert to float and append as a tuple
            data.append((entry_id, float(latitude), float(longitude)))
            
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
    except Exception as e:
        print(f"Error: {e}")
    
    return data

def create_interactive_map(data, images_folder, output_file='interactive_map.html'):
    # create a Folium map
    folium_map = folium.Map(location=[0, 0], zoom_start=2)
    
    for entry_id, lat, lon in data:
        marker_color = 'red'
        # check if an image exists for the ID
        image_path = os.path.join(images_folder, f"{entry_id}.png")
        if os.path.exists(image_path) and 0:

            # create an HTML string to embed the image
            popup_html = f'<img src="{image_path}" width="200">'
        else:
            # fallback to displaying the ID
            popup_html = f"<b>ID:</b> {entry_id}"
        
        # add a marker with the popup
        folium.Marker(location=[lat, lon], popup=folium.Popup(popup_html, max_width=300),icon=folium.Icon(color=marker_color)).add_to(folium_map)
    
    # save the map to an HTML file
    folium_map.save(output_file)

def main(file_path, images_folder):
    # extract data from the XML file
    data = extract_coordinates_and_ids(file_path)
    # create the interactive map
    create_interactive_map(data, images_folder)

if __name__ == "__main__":
    file_path = "coordinates.xml"
    images_folder = "images"
    main(file_path, images_folder)
