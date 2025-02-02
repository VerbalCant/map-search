import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from haversine import haversine

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class USASpendingAPI:
    """Handler for USAspending.gov API interactions."""
    
    BASE_URL = "https://api.usaspending.gov/api/v2"
    
    def __init__(self, radius_miles: float = 50):
        """Initialize the API handler.
        
        Args:
            radius_miles: Search radius in miles for location-based queries
        """
        self.radius_miles = radius_miles
        self.cache_file = "contract_cache.json"
        self._load_cache()
    
    def _load_cache(self):
        """Load the contract search cache."""
        try:
            with open(self.cache_file, 'r') as f:
                self.cache = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.cache = {}
            self._save_cache()
    
    def _save_cache(self):
        """Save the contract search cache."""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def _get_cache_key(self, lat: float, lon: float) -> str:
        """Generate a cache key for a location."""
        return f"{lat:.4f}_{lon:.4f}_{self.radius_miles}"
    
    def _get_state_from_coords(self, latitude: float, longitude: float) -> str:
        """Get state abbreviation from coordinates using reverse geocoding."""
        try:
            location = requests.get(
                f"https://api.usaspending.gov/api/v2/recipient/state/{latitude}/{longitude}/"
            ).json()
            return location.get("state_code", "NV")  # Default to Nevada if not found
        except:
            return "NV"  # Default to Nevada on error
    
    def search_contracts_by_location(
        self,
        latitude: float,
        longitude: float,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        bust_cache: bool = False
    ) -> List[Dict]:
        """Search for contracts near a specific location."""
        cache_key = self._get_cache_key(latitude, longitude)
        
        if not bust_cache and cache_key in self.cache:
            logger.info(f"ALAINA: Using cached contract results for location ({latitude}, {longitude})")
            return self.cache[cache_key]
        
        # Default to last 10 years if dates not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=10*365)).strftime("%Y-%m-%d")
        
        # Get state from coordinates
        state_code = self._get_state_from_coords(latitude, longitude)
        
        payload = {
            "filters": {
                "award_type_codes": ["A", "B", "C", "D"],
                "time_period": [
                    {
                        "start_date": start_date,
                        "end_date": end_date
                    }
                ],
                "place_of_performance_locations": [
                    {
                        "country": "USA",
                        "state": state_code
                    }
                ]
            },
            "fields": [
                "Award ID",
                "Recipient Name",
                "Award Amount",
                "Start Date",
                "End Date",
                "Place of Performance Zip5",
                "Description",
                "Awarding Agency",
                "Funding Agency",
                "Place of Performance State Code",
                "Place of Performance City Code"
            ],
            "page": 1,
            "limit": 100,  # Maximum allowed by API
            "sort": "Award Amount",
            "order": "desc"
        }
        
        try:
            logger.info(f"ALAINA: Searching contracts in {state_code} near ({latitude}, {longitude})")
            response = requests.post(
                f"{self.BASE_URL}/search/spending_by_award/",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "location_analyzer/1.0"
                }
            )
            
            if response.status_code != 200:
                logger.error(f"ALAINA: API Error: {response.status_code}")
                logger.error(f"ALAINA: Response: {response.text}")
                return []
                
            data = response.json()
            all_results = data.get("results", [])
            
            logger.info(f"ALAINA: Found {len(all_results)} total contracts in {state_code}")
            
            # Filter results by distance using ZIP code prefix (first 3 digits for broader area)
            filtered_results = []
            for result in all_results:
                try:
                    # Get ZIP code from place of performance
                    perf_zip = result.get("Place of Performance Zip5", "")
                    if not perf_zip or len(perf_zip) < 3:
                        continue
                        
                    # Use first 3 digits of ZIP for broader area matching
                    # Nevada ZIP codes: 890-891 Las Vegas area, 893-895 Reno area, 889 rural areas
                    if perf_zip[:3] in ["890", "891", "893", "894", "895", "889"]:
                        filtered_results.append(result)
                except:
                    continue
            
            if filtered_results:
                logger.info(f"ALAINA: Found {len(filtered_results)} relevant contracts in the area")
                
                # Log some details about the contracts
                total_value = sum(float(r.get("Award Amount", 0)) for r in filtered_results)
                logger.info(f"ALAINA: Total contract value: ${total_value:,.2f}")
                
                # Log unique agencies
                agencies = set(r.get("Awarding Agency", "") for r in filtered_results)
                logger.info("ALAINA: Awarding agencies found:")
                for agency in agencies:
                    if agency:
                        logger.info(f"ALAINA:   - {agency}")
                        
                # Log some contract descriptions
                logger.info("ALAINA: Sample contract descriptions:")
                for result in filtered_results[:3]:  # Show first 3 descriptions
                    desc = result.get("Description", "").strip()
                    if desc:
                        logger.info(f"ALAINA:   - {desc[:200]}...")  # Truncate long descriptions
            else:
                logger.info("ALAINA: No contracts found in the specified area")
            
            # Cache the results
            self.cache[cache_key] = filtered_results
            self._save_cache()
            
            return filtered_results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"ALAINA: Error searching contracts: {str(e)}")
            if hasattr(e.response, 'text'):
                logger.error(f"ALAINA: Response details: {e.response.text}")
            return []
    
    def analyze_contracts(self, contracts: List[Dict]) -> Dict:
        """Analyze contract data to extract insights.
        
        Args:
            contracts: List of contract dictionaries
            
        Returns:
            Dictionary containing analysis results
        """
        if not contracts:
            return {
                "total_contracts": 0,
                "total_value": 0,
                "top_contractors": [],
                "summary": "No contracts found in this area."
            }
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(contracts)
        
        # Basic analysis
        analysis = {
            "total_contracts": len(contracts),
            "total_value": df["Award Amount"].sum(),
            "top_contractors": df.groupby("Recipient Name")["Award Amount"].sum().nlargest(5).to_dict(),
            "summary": f"Found {len(contracts)} contracts worth ${df['Award Amount'].sum():,.2f}"
        }
        
        return analysis 