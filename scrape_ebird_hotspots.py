import pandas as pd
import gspread
from geopy.geocoders import Nominatim
import time
from gspread_dataframe import set_with_dataframe
from ebird.api import get_nearby_hotspots, get_observations
from geopy.exc import GeocoderServiceError
import json

# Read the configuration from the file
with open('config.json') as config_file:
    config = json.load(config_file)

# Access the values
google_api_key = config['google_api_key']
ebird_api_key = config['ebird_api_key']
my_location = config['location']

# Get the current latitude and longitude of your location
geolocator = Nominatim(user_agent="my-app", timeout=10)
max_retries = 3
retry_delay = 2  # seconds

for attempt in range(max_retries):
    try:
        location = geolocator.geocode(my_location)
        latitude = location.latitude
        longitude = location.longitude
        break  # Break the loop if successful
    except GeocoderServiceError as e:
        print(f"Error: {e}")
        if attempt < max_retries - 1:
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        else:
            print("Maximum number of retries reached. Exiting.")
            raise

# Specify the distance and time range for observations
distance = 10  # Distance in kilometers
time_range = 3  # Time range in days

# Get nearby hotspots
hotspots = get_nearby_hotspots(ebird_api_key, latitude, longitude, dist=distance, back=time_range)

if hotspots is not None:
    df_hotspots = pd.json_normalize(hotspots)

    # Use your service account to authenticate with Google Drive and Sheets
    gc = gspread.service_account(filename='google.json')

    # Open the Google Sheet (replace with your own)
    sh = gc.open_by_key(google_api_key)

    # Select the 'hotspots' worksheet
    worksheet_hotspots = sh.worksheet('hotspots')

    # Clear existing data in the 'hotspots' worksheet
    worksheet_hotspots.clear()

    # Write the DataFrame to the 'hotspots' worksheet
    set_with_dataframe(worksheet_hotspots, df_hotspots, include_index=False)

    if 'locId' in df_hotspots.columns:
        locids = df_hotspots['locId'].tolist()

        # Create an empty DataFrame to store the observations
        df_observations = pd.DataFrame()

        # Batch the locid in groups of 10
        batch_size = 10
        locid_batches = [locids[i:i + batch_size] for i in range(0, len(locids), batch_size)]

        # Loop through the locid batches and get observations for each batch
        for locid_batch in locid_batches:
            observations = get_observations(api_key, locid_batch)
            print(observations)
            if observations is not None:
                df_batch = pd.json_normalize(observations)
                df_observations = pd.concat([df_observations, df_batch], ignore_index=True)

        df_observations.insert(2, 'URL', 'https://www.allaboutbirds.org/guide/' + df_observations['comName'].str.replace(' ', '_') + '/photo-gallery')


        # Select the 'hotspot_observations' worksheet
        worksheet_observations = sh.worksheet('hotspot_observations')

        # Clear existing data in the 'hotspot_observations' worksheet
        worksheet_observations.clear()

        # Write the DataFrame to the 'hotspot_observations' worksheet
        set_with_dataframe(worksheet_observations, df_observations, include_index=False)

    else:
        print("No 'locId' column in the DataFrame.")

else:
    print("No data to write to the spreadsheet.")
