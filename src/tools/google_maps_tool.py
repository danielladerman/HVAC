import os
import time
import googlemaps
from dotenv import load_dotenv

load_dotenv()

class GoogleMapsTool:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not self.api_key:
            raise ValueError("Google Maps API key is required. Please set the GOOGLE_MAPS_API_KEY environment variable.")
        self.gmaps = googlemaps.Client(key=self.api_key)

    def find_hvac_companies(self, location: str, max_leads: int = 50, existing_websites: set = set()) -> dict:
        """
        Finds multiple HVAC companies in a specific location and returns their details,
        skipping any companies whose website is in the existing_websites set.
        """
        query = f"HVAC companies in {location}"
        places_result = self.gmaps.places(query=query)
        leads = []
        
        while len(leads) < max_leads and places_result:
            for place in places_result.get('results', []):
                place_id = place.get('place_id')
                if not place_id:
                    continue

                # Fetch detailed information for the specific place
                fields = ['name', 'website', 'formatted_phone_number']
                place_details = self.gmaps.place(place_id=place_id, fields=fields).get('result', {})
                
                website = place_details.get('website')
                if website in existing_websites:
                    print(f"Skipping existing lead: {place_details.get('name')}")
                    continue

                # The official googlemaps library returns 'website', not 'websiteUri'
                leads.append({
                    "Business Name": place_details.get('name'),
                    "Website": website,
                    "Phone Number": place_details.get('formatted_phone_number')
                })

                if len(leads) >= max_leads:
                    break
            
            # Pagination
            if len(leads) < max_leads and 'next_page_token' in places_result:
                # The API requires a short delay before the next page token is valid
                time.sleep(2)
                places_result = self.gmaps.places(query=query, page_token=places_result['next_page_token'])
            else:
                break
                
        return {"leads": leads}