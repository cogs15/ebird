import pandas as pd
import gspread
from gspread_dataframe import set_with_dataframe
from geopy.geocoders import Nominatim
from ebird.api import get_nearby_observations
from geopy.exc import GeocoderServiceError
import time
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
max_retries = 10
retry_delay = 5  # seconds

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
distance = 8  # Distance in kilometers
time_range = 3  # Time range in days

# Fetch nearby observations using eBird API
records = get_nearby_observations(ebird_api_key, latitude, longitude, dist=distance, back=time_range)

if records is not None:
    df = pd.json_normalize(records)
    #df.drop_duplicates(inplace=True)  # De-duplicate the data
    df.insert(2, 'URL', 'https://www.allaboutbirds.org/guide/' + df['comName'].str.replace(' ', '_') + '/photo-gallery')
    print(df)

    # Use your service account to authenticate with Google Drive and Sheets
    gc = gspread.service_account(filename='google.json')

    # Open the Google Sheet (replace with your own)
    sh = gc.open_by_key(google_api_key)

    # Select the 'output' worksheet
    worksheet = sh.worksheet('nearby')

    # Clear existing data in the 'output' worksheet
    worksheet.clear()

    # Write the DataFrame to the 'output' worksheet
    set_with_dataframe(worksheet, df, include_index=False)

else:
    print("No data to write to the spreadsheet.")
