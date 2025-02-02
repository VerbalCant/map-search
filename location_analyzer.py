import os
import argparse
from pykml import parser
from duckduckgo_search import DDGS
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from typing import Dict, List, Tuple
import logging
from lxml import etree

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
    def __init__(self, kml_file_path: str, max_places: int = None, debug: bool = False):
        """Initialize the LocationAnalyzer with a KML file path."""
        self.kml_file_path = kml_file_path
        self.max_places = max_places
        self.debug = debug
        self.locations = []
        self.geolocator = Nominatim(user_agent="location_analyzer")
        
        if self.debug:
            logger.setLevel(logging.DEBUG)
        
        logger.debug(f"ALAINA: Initializing LocationAnalyzer with file: {kml_file_path}")
        logger.debug(f"ALAINA: Max places to process: {max_places if max_places else 'All'}")
        
        # Download required NLTK data
        try:
            nltk.download('punkt')
            nltk.download('averaged_perceptron_tagger')
            nltk.download('maxent_ne_chunker')
            nltk.download('words')
        except LookupError as e:
            logger.error(f"ALAINA: Error downloading NLTK data: {str(e)}")

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

    def search_location_context(self, max_results: int = 5) -> List[Dict]:
        """Search the internet for relevant information about each location."""
        search_results = []
        
        for location in self.locations:
            logger.info(f"ALAINA: Searching for information about {location['name']}")
            
            # Construct search queries based on context
            queries = self._generate_search_queries(location)
            logger.debug(f"ALAINA: Generated queries: {queries}")
            location_results = []
            
            with DDGS() as ddgs:
                for query in queries:
                    try:
                        logger.debug(f"ALAINA: Executing search query: {query}")
                        results = list(ddgs.text(query, max_results=max_results))
                        location_results.extend(results)
                    except Exception as e:
                        logger.error(f"ALAINA: Error during search for {query}: {str(e)}")
                        continue
            
            search_results.append({
                'location': location['name'],
                'results': location_results
            })
        
        return search_results

    def _generate_search_queries(self, location: Dict) -> List[str]:
        """Generate relevant search queries based on location context."""
        queries = []
        
        # Basic location query
        queries.append(f"{location['name']} location history")
        
        # Add organization-specific queries
        for org in location['context']['organizations']:
            queries.append(f"{org} {location['name']} development")
        
        # Add location-specific queries
        for loc in location['context']['locations']:
            queries.append(f"{loc} {location['name']} news")
        
        # Add key terms queries
        key_terms = ' '.join(location['context']['key_terms'][:3])  # Use top 3 key terms
        if key_terms:
            queries.append(f"{location['name']} {key_terms}")
        
        # Add coordinates-based query if available
        if location['coordinates']:
            coords = location['coordinates']
            queries.append(f"location near {coords['lat']},{coords['lon']}")
        
        return queries

def main():
    """Main function to demonstrate usage."""
    parser = argparse.ArgumentParser(description='Analyze locations from a KML file')
    parser.add_argument('--kml-file', default="Imminent_Domain.kml",
                      help='Path to the KML file (default: Imminent_Domain.kml)')
    parser.add_argument('--max-places', type=int,
                      help='Maximum number of places to process (default: all)')
    parser.add_argument('--debug', action='store_true',
                      help='Enable debug logging')
    parser.add_argument('--max-results', type=int, default=5,
                      help='Maximum number of search results per query (default: 5)')
    
    args = parser.parse_args()
    
    try:
        analyzer = LocationAnalyzer(args.kml_file, args.max_places, args.debug)
        analyzer.parse_kml()
        
        # Search for information about each location
        results = analyzer.search_location_context(max_results=args.max_results)
        
        # Print results
        for location_result in results:
            logger.info(f"ALAINA: Results for {location_result['location']}:")
            for idx, result in enumerate(location_result['results'], 1):
                logger.info(f"ALAINA: Result {idx}:")
                logger.info(f"ALAINA: Title: {result.get('title', 'N/A')}")
                logger.info(f"ALAINA: Link: {result.get('link', 'N/A')}")
                logger.info(f"ALAINA: Snippet: {result.get('body', 'N/A')}\n")

    except Exception as e:
        logger.error(f"ALAINA: An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 