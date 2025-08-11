# Authors: Lucas Holliday, Sid Javeri, Helena Yuan
#
# Paramaters team name, year
#
# Retrieves the stored team statistics from the RDS database based on user inputs.
# Returns statistics in body.
#

import json
import requests
from datetime import datetime, timedelta
import urllib.parse

# Replace with your actual API key
TICKETMASTER_API_KEY = "API_KEY"

def lambda_handler(event, context):
    try:
        # Define the Ticketmaster API URL (Example: fetching events)
        params = event["pathParameters"]
        postal = str(params["city"])
        decoded_postal = urllib.parse.unquote(postal)

        print("postal: " + postal)
        #postal = "97205"

        current_date = datetime.now()
        three_weeks_later = current_date + timedelta(weeks=3)
        start_date = current_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_date = three_weeks_later.strftime("%Y-%m-%dT%H:%M:%SZ")

        print("building request " + str(postal))
        size = 200
        radius = 100

        url = "https://app.ticketmaster.com/discovery/v2/events.json"
        query_params = {
            "apikey": TICKETMASTER_API_KEY,
            "city": decoded_postal,
            #"postalCode": postal,
            "radius": str(radius),  # Search within 100 miles
            "size": str(size),  # Fetch up to 10 events
            "keyword": "Basketball",
            "classificationName": "Sports",  # Ensure it's in the sports category
            "sort": "date,asc",
            "startDateTime": start_date,
            "endDateTime": end_date,
        }

        response = requests.get(url, params=query_params)

        if response.status_code != 200:
            return {
                'statusCode': response.status_code,
                'body': json.dumps({"error": "Failed to fetch events from Ticketmaster API"})
            }
        
        body = response.json()

        try:
            events = body["_embedded"]["events"]
        except:
            return {
                'statusCode': 204,
                'body': "no games"
            }

        games_list = []

        for game in events:
            name = gameUrl = date = time = minPrice = maxPrice = venue = address = "N/A" 
            try: name = game["name"]
            except (KeyError, IndexError, TypeError): pass

            try: gameUrl = game["url"]
            except (KeyError, IndexError, TypeError): pass
            
            try: date = game["dates"]["start"]["localDate"]
            except (KeyError, IndexError, TypeError): pass

            try: time = game["dates"]["start"]["localTime"]
            except (KeyError, IndexError, TypeError): pass

            try: minPrice = game["priceRanges"][0]["min"]
            except (KeyError, IndexError, TypeError): pass

            try: maxPrice = game["priceRanges"][0]["max"]
            except (KeyError, IndexError, TypeError): pass

            try: venue = game["_embedded"]["venues"][0]["name"]
            except (KeyError, IndexError, TypeError): pass

            try: address = game["_embedded"]["venues"][0]["address"]["line1"]
            except (KeyError, IndexError, TypeError): pass

            try:
                if date == "N/A":
                    dateObject = datetime.max
                    formatted_date = "N/A"
                else:
                    dateObject = datetime.strptime(date, "%Y-%m-%d")
                    formatted_date = dateObject.strftime("%B %d, %Y")
            except ValueError:
                dateObject = datetime.max
                formatted_date = "N/A"

            try:
                if time == "N/A":
                    formatted_time = "N/A"
                else:
                    formatted_time = datetime.strptime(time, "%H:%M:%S").strftime("%-I:%M %p")
            except ValueError:
                formatted_time = "N/A"

            games_list.append((name, time, formatted_time, date, formatted_date, minPrice, maxPrice, gameUrl, venue, address))

        print("returning response")
        return {
            'statusCode': 200,
            'body': json.dumps(games_list)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({"error": str(e)})
        }

