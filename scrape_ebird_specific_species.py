import pandas as pd
import gspread
from gspread_dataframe import set_with_dataframe
from geopy.geocoders import Nominatim
from ebird.api import get_species_observations, get_nearest_species
# Read the configuration from the file
with open('config.json') as config_file:
    config = json.load(config_file)

# Access the values
google_api_key = config['google_api_key']
ebird_api_key = config['ebird_api_key']
my_location = config['location']

# Get the current latitude and longitude of your location
geolocator = Nominatim(user_agent="my-app")
location = geolocator.geocode(my_location)
latitude = location.latitude
longitude = location.longitude

# Specify the distance and time range for observations
distance = 2  # Distance in kilometers
time_range = 3  # Time range in days

# Fetch nearby observations using eBird API
species = 'perfal'
distance = 25  # Distance in kilometers
records = get_nearest_species(ebird_api_key, species, latitude, longitude, distance)

if records is not None:
    df = pd.json_normalize(records)
    #df.drop_duplicates(inplace=True)  # De-duplicate the data

    print(df)

    # Use your service account to authenticate with Google Drive and Sheets
    gc = gspread.service_account(filename='google.json')

    # Open the Google Sheet (replace with your own)
    sh = gc.open_by_key(google_api_key)

    # Select the 'output' worksheet
    worksheet = sh.worksheet('species')

    # Clear existing data in the 'output' worksheet
    worksheet.clear()

    # Write the DataFrame to the 'output' worksheet
    set_with_dataframe(worksheet, df, include_index=False)

else:
    print("No data to write to the spreadsheet.")
