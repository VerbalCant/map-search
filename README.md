# Location Search Tool

A Python tool for analyzing location data from KML files and gathering contextual information about the locations using web searches.

## Features

- Parse KML files containing placemarks with location data
- Extract location names, coordinates, and viewing parameters
- Analyze location context using natural language processing
- Search for additional information about locations using DuckDuckGo
- Support for both standard KML name tags and custom n tags
- Detailed logging for debugging and tracking

## Requirements

- Python 3.7+
- Required Python packages (install via pip):
  - pykml
  - duckduckgo_search
  - geopy
  - nltk
  - lxml

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/battelle_location_search.git
cd battelle_location_search
```

2. Create and activate a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install pykml duckduckgo_search geopy nltk lxml
```

4. Download required NLTK data:
```python
python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger'); nltk.download('maxent_ne_chunker'); nltk.download('words')"
```

## Usage

Basic usage:
```bash
python location_analyzer.py --kml-file your_file.kml
```

Options:
- `--kml-file`: Path to the KML file (default: "Imminent_Domain.kml")
- `--max-places`: Maximum number of places to process (default: all)
- `--debug`: Enable debug logging
- `--max-results`: Maximum number of search results per query (default: 5)

Example with all options:
```bash
python location_analyzer.py --kml-file locations.kml --max-places 10 --debug --max-results 3
```

## Output

The tool provides:
1. Extracted location information including:
   - Location names
   - Coordinates (latitude/longitude)
   - View parameters (altitude, range, heading, tilt)
   - Extended data if available
2. Contextual information:
   - Organizations mentioned
   - Related locations
   - Key terms
3. Search results from DuckDuckGo for each location

## Logging

- Info level: Basic progress and results
- Debug level: Detailed information about each step (enable with --debug)
- All logs include timestamp and level
- Format: "ALAINA: [message]" for easy filtering

## Error Handling

- Graceful handling of missing KML tags
- Fallback options for name extraction
- Rate limiting handling for web searches
- Comprehensive error logging

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 