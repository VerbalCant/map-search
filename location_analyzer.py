import os
import argparse
from pykml import parser
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from typing import Dict, List, Tuple
import logging
from lxml import etree
import time
from random import uniform
from serpapi import GoogleSearch
import json
from datetime import datetime
import hashlib
from dotenv import load_dotenv
import requests
from usaspending_api import USASpendingAPI

# Load environment variables from .env.local first, then fall back to .env
load_dotenv('.env.local')
load_dotenv('.env')  # This won't override variables that were already loaded

# Set up logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define XML namespaces
KML_NS = {
    'kml': "http://www.opengis.net/kml/2.2",
    'gx': "http://www.google.com/kml/ext/2.2"
}

class LocationAnalyzer:
    def __init__(self, kml_file_path: str, max_places: int = None, debug: bool = False, bust_cache: bool = False, search_radius_miles: float = 50):
        """Initialize the LocationAnalyzer with a KML file path."""
        self.kml_file_path = kml_file_path
        self.max_places = max_places
        self.debug = debug
        self.bust_cache = bust_cache
        self.search_radius_miles = search_radius_miles
        self.locations = []
        self.geolocator = Nominatim(user_agent="location_analyzer")
        self.api_key = os.getenv("SERPAPI_KEY")
        if not self.api_key:
            raise ValueError("SERPAPI_KEY environment variable not set")
        
        # Initialize USASpending API client
        self.contract_api = USASpendingAPI(radius_miles=search_radius_miles)
        
        # Initialize results storage
        self.contract_results = {}
        
        # Validate API key before proceeding
        if not self._validate_api_key():
            raise ValueError("Invalid SERPAPI_KEY - please check your API key at https://serpapi.com/manage-api-key")
        
        self.max_retries = 3
        self.base_delay = 2  # Base delay in seconds
        
        # Set up cache and API tracking files
        self.cache_file = "search_cache.json"
        self.api_log_file = "api_usage.log"
        self.cache = self._load_cache()
        
        if self.debug:
            logger.setLevel(logging.DEBUG)
        
        logger.debug(f"ALAINA: Initializing LocationAnalyzer with file: {kml_file_path}")
        logger.debug(f"ALAINA: Cache busting enabled: {bust_cache}")
        logger.debug(f"ALAINA: Max places to process: {max_places if max_places else 'All'}")
        
        # Download required NLTK data
        try:
            nltk.download('punkt')
            nltk.download('averaged_perceptron_tagger')
            nltk.download('maxent_ne_chunker')
            nltk.download('words')
        except LookupError as e:
            logger.error(f"ALAINA: Error downloading NLTK data: {str(e)}")

    def _validate_api_key(self) -> bool:
        """Validate the API key by making a test request."""
        try:
            logger.info("ALAINA: Validating API key...")
            url = "https://www.searchapi.io/api/v1/me"
            headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                logger.info("ALAINA: API key validation successful")
                return True
            else:
                logger.error(f"ALAINA: API key validation failed with status code {response.status_code}")
                logger.error(f"ALAINA: Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"ALAINA: API key validation failed with error: {str(e)}")
            return False

    def _load_cache(self) -> Dict:
        """Load the search cache from file."""
        if self.bust_cache:
            logger.info("ALAINA: Cache busting enabled - starting with empty cache")
            return {}
            
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"ALAINA: Error loading cache: {str(e)}")
        return {}

    def _save_cache(self) -> None:
        """Save the search cache to file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
            logger.info("ALAINA: Cache saved successfully")
        except Exception as e:
            logger.error(f"ALAINA: Error saving cache: {str(e)}")

    def _log_api_usage(self, query: str, success: bool) -> None:
        """Log API usage with timestamp and details."""
        try:
            timestamp = datetime.now().isoformat()
            log_entry = {
                'timestamp': timestamp,
                'query': query,
                'success': success,
                'api_key_last_4': self.api_key[-4:] if self.api_key else 'none'
            }
            
            with open(self.api_log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
            logger.info(f"ALAINA: API call logged - Success: {success}")
        except Exception as e:
            logger.error(f"ALAINA: Error logging API usage: {str(e)}")

    def _generate_cache_key(self, query: str, location: Dict) -> str:
        """Generate a unique cache key for a search query."""
        # Include location coordinates in cache key if available
        coords_str = ''
        if location.get('coordinates'):
            coords = location['coordinates']
            coords_str = f"_{coords['lat']}_{coords['lon']}"
            
        # Create a unique key based on query and coordinates
        key_string = f"{query}{coords_str}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def parse_kml(self) -> None:
        """Parse the KML file and extract location information."""
        logger.info("ALAINA: Starting KML file parsing")
        
        try:
            with open(self.kml_file_path, 'rb') as kml_file:
                logger.debug("ALAINA: Reading KML file")
                tree = parser.parse(kml_file)
                root = tree.getroot()
                
                # Extract Placemarks using proper namespace
                placemarks = root.findall(".//kml:Placemark", namespaces=KML_NS)
                total_placemarks = len(placemarks)
                logger.info(f"ALAINA: Found {total_placemarks} total placemarks")
                
                # Limit placemarks if max_places is set
                if self.max_places:
                    placemarks = placemarks[:self.max_places]
                    logger.info(f"ALAINA: Processing first {self.max_places} placemarks")
                
                for idx, placemark in enumerate(placemarks, 1):
                    logger.debug(f"ALAINA: Processing placemark {idx}/{len(placemarks)}")
                    location_info = self._extract_placemark_info(placemark)
                    if location_info:
                        self.locations.append(location_info)
                        logger.info(f"ALAINA: Found location: {location_info['name']}")
                        if self.debug:
                            logger.debug(f"ALAINA: Location details: {location_info}")
                        
            logger.info(f"ALAINA: Successfully parsed {len(self.locations)} locations from KML file")
        except Exception as e:
            logger.error(f"ALAINA: Error parsing KML file: {str(e)}")
            raise

    def _extract_placemark_info(self, placemark) -> Dict:
        """Extract relevant information from a placemark."""
        try:
            # Get name from either name or n tag using proper namespace
            name = None
            # Try name tag first
            name_tag = placemark.find(".//kml:name", namespaces=KML_NS)
            if name_tag is not None and name_tag.text:
                name = name_tag.text.strip()
                logger.debug(f"ALAINA: Found name tag with value: {name}")
            
            # If no name tag found, try n tag
            if not name:
                n_tag = placemark.find("n")  # Try without namespace first
                if n_tag is None:
                    n_tag = placemark.find(".//kml:n", namespaces=KML_NS)  # Try with namespace
                
                if n_tag is not None and n_tag.text:
                    name = n_tag.text.strip()
                    logger.debug(f"ALAINA: Found n tag with value: {name}")
            
            if not name:
                name = 'Unknown Location'
                logger.debug("ALAINA: No name found, using 'Unknown Location'")
            
            # Get coordinates from either Point or Polygon using proper namespace
            coords = None
            point = placemark.find(".//kml:Point", namespaces=KML_NS)
            polygon = placemark.find(".//kml:Polygon", namespaces=KML_NS)
            
            if point is not None:
                logger.debug("ALAINA: Found Point geometry")
                coords_elem = point.find(".//kml:coordinates", namespaces=KML_NS)
                if coords_elem is not None and coords_elem.text:
                    coords_text = coords_elem.text.strip()
                    coords_parts = coords_text.split(',')
                    coords = {'lat': float(coords_parts[1]), 'lon': float(coords_parts[0])}
                    logger.debug(f"ALAINA: Extracted coordinates: {coords}")
            elif polygon is not None:
                logger.debug("ALAINA: Found Polygon geometry")
                outer_boundary = polygon.find(".//kml:outerBoundaryIs", namespaces=KML_NS)
                if outer_boundary is not None:
                    linear_ring = outer_boundary.find(".//kml:LinearRing", namespaces=KML_NS)
                    if linear_ring is not None:
                        coords_elem = linear_ring.find(".//kml:coordinates", namespaces=KML_NS)
                        if coords_elem is not None and coords_elem.text:
                            # Take the first coordinate pair from the polygon
                            coords_text = coords_elem.text.strip().split()[0]
                            coords_parts = coords_text.split(',')
                            coords = {'lat': float(coords_parts[1]), 'lon': float(coords_parts[0])}
                            logger.debug(f"ALAINA: Extracted first polygon coordinate: {coords}")
            
            # Get extended data if available
            extended_data = {}
            ext_data = placemark.find(".//kml:ExtendedData", namespaces=KML_NS)
            if ext_data is not None:
                logger.debug("ALAINA: Found ExtendedData")
                for data in ext_data.findall(".//kml:Data", namespaces=KML_NS):
                    name_attr = data.get('name')
                    value_elem = data.find(".//kml:value", namespaces=KML_NS)
                    if name_attr and value_elem is not None and value_elem.text:
                        extended_data[name_attr] = value_elem.text
                        logger.debug(f"ALAINA: Found extended data: {name_attr} = {value_elem.text}")
            
            # Get LookAt data for additional context
            look_at = placemark.find(".//kml:LookAt", namespaces=KML_NS)
            if look_at is not None:
                logger.debug("ALAINA: Found LookAt data")
                for elem_name in ['altitude', 'range', 'heading', 'tilt']:
                    elem = look_at.find(f".//kml:{elem_name}", namespaces=KML_NS)
                    if elem is not None and elem.text:
                        extended_data[f'view_{elem_name}'] = elem.text
                        logger.debug(f"ALAINA: Found view {elem_name}: {elem.text}")
            
            # Extract context without relying on POS tagging if it fails
            try:
                context = self._extract_context(name)
                logger.debug(f"ALAINA: Extracted context: {context}")
            except Exception as e:
                logger.error(f"ALAINA: Error extracting context: {str(e)}")
                context = {
                    'organizations': [],
                    'locations': [],
                    'key_terms': [name]  # At least include the name as a key term
                }
            
            return {
                'name': name,
                'coordinates': coords,
                'extended_data': extended_data,
                'context': context
            }
        except Exception as e:
            logger.error(f"ALAINA: Error extracting placemark info: {str(e)}")
            return None

    def _extract_context(self, name: str) -> Dict:
        """Extract contextual information from location name."""
        logger.debug(f"ALAINA: Extracting context from name: {name}")
        
        # Split name into words and clean them
        words = [w.strip() for w in name.split() if len(w.strip()) > 2]
        
        context = {
            'organizations': [],
            'locations': [],
            'key_terms': []
        }
        
        # Add all words as key terms
        context['key_terms'] = words
        logger.debug(f"ALAINA: Found key terms: {context['key_terms']}")
        
        # Try to identify organizations and locations
        for word in words:
            if self._is_likely_organization(word):
                context['organizations'].append(word)
                logger.debug(f"ALAINA: Found organization: {word}")
            elif self._is_likely_location(word):
                context['locations'].append(word)
                logger.debug(f"ALAINA: Found location: {word}")
        
        return context

    def _is_likely_organization(self, term: str) -> bool:
        """Simple heuristic to identify if a term is likely an organization."""
        org_indicators = ['Inc', 'Corp', 'LLC', 'Ltd', 'Company', 'Association']
        return any(indicator in term for indicator in org_indicators)

    def _is_likely_location(self, term: str) -> bool:
        """Attempt to verify if a term is a location using geocoding."""
        try:
            logger.debug(f"ALAINA: Geocoding term: {term}")
            location = self.geolocator.geocode(term, timeout=5)
            return location is not None
        except GeocoderTimedOut:
            logger.warning(f"ALAINA: Geocoding timed out for term: {term}")
            return False

    def _generate_search_queries(self, location: Dict) -> List[str]:
        """Generate a single optimized search query for the location."""
        name = location['name']
        queries = []
        
        # Split the name into parts and use meaningful words
        words = [w for w in name.split() if len(w) > 2 and w.lower() not in ['the', 'and', 'test', 'model', 'city']]
        
        # Create a query focusing on the location name
        if words:
            # Use the first two meaningful words if available
            if len(words) >= 2:
                main_query = f"{words[0]} {words[1]}"
            else:
                main_query = words[0]
        else:
            main_query = name
            
        # Add Nevada context since we know it's in Clark County, Nevada
        main_query += " Nevada"
            
        queries.append(main_query)
        logger.info(f"ALAINA: Generated search query: {main_query}")
        return queries

    def _search_with_retry(self, query: str, location: Dict, max_results: int) -> List[Dict]:
        """Execute a search with retry logic and caching."""
        cache_key = self._generate_cache_key(query, location)
        
        # Check cache first
        if not self.bust_cache and cache_key in self.cache:
            logger.info("ALAINA: Using cached results for query")
            return self.cache[cache_key]

        for attempt in range(self.max_retries):
            try:
                logger.info(f"ALAINA: Executing search query: {query} (attempt {attempt + 1}/{self.max_retries})")
                
                # Build search parameters
                url = "https://www.searchapi.io/api/v1/search"
                headers = {
                    "Accept": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                params = {
                    "engine": "google",
                    "q": query,
                    "num": max_results,
                    "gl": "us",
                    "hl": "en"
                }
                
                # Add location biasing if coordinates are available
                if location.get('coordinates'):
                    coords = location['coordinates']
                    # Try to get a location name for these coordinates
                    try:
                        location_name = self.geolocator.reverse((coords['lat'], coords['lon']))
                        if location_name:
                            params.update({
                                "location": str(location_name),
                                "google_domain": "google.com"
                            })
                            logger.info(f"ALAINA: Using location: {location_name}")
                    except Exception as e:
                        logger.warning(f"ALAINA: Could not reverse geocode coordinates: {str(e)}")
                        # Fallback to using Clark County, Nevada
                        params.update({
                            "location": "Clark County, Nevada, United States",
                            "google_domain": "google.com"
                        })
                        logger.info("ALAINA: Using fallback location: Clark County, Nevada")
                
                response = requests.get(url, headers=headers, params=params)
                
                if response.status_code != 200:
                    raise Exception(f"Search API returned status code {response.status_code}: {response.text}")
                
                results = response.json()
                
                # Debug raw response
                logger.debug(f"ALAINA: Raw API response: {json.dumps(results, indent=2)}")
                
                # Extract and format organic results
                formatted_results = []
                for result in results.get("organic_results", []):
                    formatted_results.append({
                        'title': result.get('title', ''),
                        'link': result.get('link', ''),
                        'body': result.get('snippet', '')
                    })
                
                # Cache successful results
                self.cache[cache_key] = formatted_results
                self._save_cache()
                
                # Log successful API call
                self._log_api_usage(query, True)
                
                return formatted_results
                
            except Exception as e:
                logger.error(f"ALAINA: Error during search for {query}: {str(e)}")
                # Log failed API call
                self._log_api_usage(query, False)
                
                if "quota" in str(e).lower():
                    logger.error("ALAINA: SerpAPI quota exceeded")
                    return []
                
                delay = self.base_delay * (2 ** attempt)
                logger.warning(f"ALAINA: Search failed, waiting {delay} seconds before retry")
                time.sleep(delay)
                continue
        
        logger.error(f"ALAINA: Max retries reached for query: {query}")
        return []

    def search_location_context(self, max_results: int = 5) -> List[Dict]:
        """Search for relevant information about each location."""
        search_results = []
        
        for location in self.locations:
            logger.info(f"ALAINA: Searching for information about {location['name']}")
            
            # Generate single optimized query
            queries = self._generate_search_queries(location)
            logger.debug(f"ALAINA: Generated query: {queries[0]}")
            
            # Single search with location biasing
            results = self._search_with_retry(queries[0], location, max_results)
            
            search_results.append({
                'location': location['name'],
                'results': results[:max_results]
            })
        
        return search_results

    def _extract_coordinates(self, placemark) -> Tuple[float, float]:
        """Extract coordinates from a KML placemark."""
        coords = placemark.Point.coordinates.text.strip().split(',')
        return float(coords[1]), float(coords[0])  # lat, lon
        
    def analyze_contracts(self, placemark) -> Dict:
        """Analyze government contracts for a location."""
        try:
            lat, lon = self._extract_coordinates(placemark)
            
            logger.info(f"ALAINA: Searching for contracts near {placemark.name.text if hasattr(placemark, 'name') else 'Unknown'} ({lat}, {lon})")
            
            # Search for contracts
            contracts = self.contract_api.search_contracts_by_location(
                latitude=lat,
                longitude=lon,
                bust_cache=self.bust_cache
            )
            
            # Analyze the results
            analysis = self.contract_api.analyze_contracts(contracts)
            
            # Store results
            self.contract_results[placemark.name.text if hasattr(placemark, 'name') else f"{lat},{lon}"] = analysis
            
            return analysis
            
        except Exception as e:
            logger.error(f"ALAINA: Error analyzing contracts for location: {str(e)}")
            return {
                "error": str(e),
                "total_contracts": 0,
                "total_value": 0,
                "top_contractors": [],
                "summary": "Error analyzing contracts for this location."
            }

def main():
    """Main function to demonstrate usage."""
    arg_parser = argparse.ArgumentParser(description="Analyze locations from a KML file")
    arg_parser.add_argument("--kml-file", default="Imminent_Domain.kml", help="Path to KML file")
    arg_parser.add_argument("--max-places", type=int, help="Maximum number of places to process")
    arg_parser.add_argument("--max-results", type=int, default=5, help="Maximum number of search results per place")
    arg_parser.add_argument("--bust-cache", action="store_true", help="Ignore cached results")
    arg_parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    arg_parser.add_argument("--search-radius", type=float, default=50, help="Search radius in miles for contract analysis")
    arg_parser.add_argument("--contracts-only", action="store_true", help="Only perform contract analysis (skip web search)")
    
    args = arg_parser.parse_args()
    
    try:
        analyzer = LocationAnalyzer(
            args.kml_file,
            max_places=args.max_places,
            debug=args.debug,
            bust_cache=args.bust_cache,
            search_radius_miles=args.search_radius
        )
        
        with open(args.kml_file, 'rb') as f:
            kml_doc = parser.parse(f).getroot()
            
        placemarks = kml_doc.findall(".//kml:Placemark", namespaces=KML_NS)
        
        if args.max_places:
            placemarks = placemarks[:args.max_places]
            
        logger.info(f"ALAINA: Processing {len(placemarks)} locations")
        
        for placemark in placemarks:
            name = placemark.name.text if hasattr(placemark, 'name') else "Unknown Location"
            logger.info(f"ALAINA: Processing {name}")
            
            # Perform contract analysis
            contract_analysis = analyzer.analyze_contracts(placemark)
            logger.info(f"ALAINA: Contract Analysis for {name}:")
            logger.info(f"ALAINA: {contract_analysis['summary']}")
            
            if contract_analysis['top_contractors']:
                logger.info("ALAINA: Top Contractors:")
                for contractor, amount in contract_analysis['top_contractors'].items():
                    logger.info(f"ALAINA:   - {contractor}: ${amount:,.2f}")
            
            # Perform web search unless contracts-only is specified
            if not args.contracts_only:
                search_results = analyzer.search_location_context(max_results=args.max_results)
                if search_results:
                    logger.info(f"ALAINA: Found {len(search_results)} web results for {name}")
            
            logger.info("ALAINA: " + "="*50)
            
    except Exception as e:
        logger.error(f"ALAINA: Error processing file: {str(e)}")
        if args.debug:
            raise
        
if __name__ == "__main__":
    main() 