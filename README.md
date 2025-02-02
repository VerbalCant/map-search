# Location Search Tool

This tool supports academic research by analyzing geographical locations from KML files and discovering relevant information through automated data collection and analysis. Originally developed to investigate organizational facilities and points of interest, it serves as a systematic approach to cross-referencing geographical data with publicly available information.

## Research Applications

This tool is particularly useful for:
1. **Systematic Data Collection**: Automates the process of gathering public information about specific geographical locations
2. **Cross-Reference Analysis**: Helps identify potential connections between locations and publicly available records
3. **Historical Research**: Enables investigation of historical significance and past activities at specific locations
4. **Pattern Analysis**: Assists in identifying geographical patterns and relationships between different locations
5. **Documentation**: Maintains a structured record of findings for academic review and verification

## Features

### 1. Location Analysis
- Processes KML files containing geographical markers and location data
- Conducts systematic internet searches for each location
- Implements caching to enable iterative research without redundant searches
- Maintains detailed logs for research reproducibility

### 2. Contract Analysis
The tool integrates with USAspending.gov's API to analyze government contracts near specified locations:

- **Geographic Coverage**: Searches contracts by state and ZIP code regions
- **Time Range**: Defaults to 10-year historical data
- **Contract Types**: Includes various award types (Contracts, Purchase Orders, Delivery Orders, etc.)
- **Data Points**: Captures key information including:
  - Award amounts and dates
  - Recipient organizations
  - Awarding/funding agencies
  - Place of performance
  - Contract descriptions

Example contract data:
```json
{
  "36.7811_-115.4435_5000.0": [
    {
      "Award ID": "DENA0003624",
      "Recipient Name": "MISSION SUPPORT & TEST SERVICES LLC",
      "Award Amount": 6096331200.02,
      "Start Date": "2017-08-01",
      "End Date": "2027-11-30",
      "Place of Performance Zip5": "89193",
      "Description": "IGF::CL,CT::IGF CONTRACT AWARD DE-NA0003624 TO THE MISSION SUPPORT AND TEST SERVICES LLC (MSTS) FOR THE MANAGEMENT AND OPERATION OF THE DEPARTMENT OF ENERGY NATIONAL NUCLEAR SECURITY ADMINISTRATION'S NEVADA NATIONAL SECURITY SITE.",
      "Awarding Agency": "Department of Energy",
      "Funding Agency": "Department of Defense"
    }
  ]
}
```

Results are cached in `contract_cache.json` using location coordinates as keys.

## What Does It Do?

1. **Reads Your Map Data**: Processes KML files containing geographical markers and location data
2. **Finds Information**: Conducts systematic internet searches for each location to gather relevant documentation
3. **Saves Time**: Implements caching to enable iterative research without redundant searches
4. **Tracks Usage**: Maintains detailed logs of all searches for research reproducibility

## Getting Started

### What You'll Need

1. Python installed on your computer
2. A SerpAPI key (for internet searches) - get one at [SerpAPI's website](https://serpapi.com/)
3. Your KML file from Google Earth

### Getting a SerpAPI Key

1. Go to [SerpAPI's website](https://serpapi.com/)
2. Click "Sign Up" and create an account
3. After signing up, you'll get your API key from your dashboard
4. SerpAPI offers:
   - Free tier: 100 searches/month
   - Paid plans: Starting from $50/month for 5,000 searches
   - Pay-as-you-go options available

### Example Output

The tool saves search results in `search_cache.json`. Here's an example of what the output looks like:

```json
{
  "e35db623840a33e01993bc53c374b9b2": [
    {
      "title": "Dog Bone Lake (Nevada)",
      "link": "https://en.wikipedia.org/wiki/Dog_Bone_Lake_(Nevada)",
      "body": "Dog Bone Lake is a dog bone-shaped topographic flat with two larger ends connected by a narrow body..."
    },
    {
      "title": "DOG BONE LAKE SOUTH, NV - USGS Store",
      "link": "https://store.usgs.gov/product/82241",
      "body": "Description: DOG BONE LAKE SOUTH, NV HISTORICAL MAP GEOPDF 7.5X7.5 GRID 24000-SCALE 1973..."
    }
  ]
}
```

The cache uses a hash of the search query as the key, and stores an array of search results with:
- `title`: The title of the search result
- `link`: The URL to the full article/page
- `body`: A snippet of relevant text

### Setup

1. Clone or download this repository to your computer
2. Open a terminal/command prompt in the folder
3. Run these commands:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. Set up your SerpAPI key:
   - Create a file named `.env` in the folder
   - Add this line: `SERPAPI_KEY=your_key_here`

## Using the Tool

Basic usage:
```bash
python location_analyzer.py --kml-file your_file.kml
```

### Available Options

- `--kml-file`: Your KML file (default: "Imminent_Domain.kml")
- `--max-places`: Limit how many places to process (e.g., `--max-places 5`)
- `--max-results`: How many search results to get per place (default: 5)
- `--bust-cache`: Get fresh results instead of using saved ones
- `--debug`: Show detailed information about what's happening
- `--search-radius`: Search radius in miles for contract analysis (default: 50)
- `--contracts-only`: Only perform contract analysis (skip web search)

Examples:
```bash
# Process just 3 places
python location_analyzer.py --max-places 3

# Get fresh results with a 5000-mile search radius
python location_analyzer.py --bust-cache --search-radius 5000

# Only analyze contracts, not web content
python location_analyzer.py --contracts-only
```

## Output Files

- `search_cache.json`: Cached web search results
- `contract_cache.json`: Cached contract search results
- `api_usage.log`: Record of all API calls and findings

## Analysis Features

### Contract Analysis
The tool provides detailed contract analysis including:
- Total contract value in the area
- Top contractors by award amount
- Awarding and funding agencies
- Contract descriptions and purposes
- Geographic distribution of contracts
- Historical contract patterns

Example analysis output:
```
Found 100 contracts worth $27,066,632,618.55
Top Contractors:
  - MISSION SUPPORT & TEST SERVICES LLC: $6,096,331,200.02
  - NATIONAL SECURITY TECHNOLOGIES, LLC: $5,634,272,220.00
  - SIERRA NEVADA COMPANY, LLC: $3,823,454,997.91
  - JT4 LLC: $2,151,340,906.83
  - BECHTEL SAIC COMPANY, LLC: $1,931,096,265.42
```

## How It Works Behind the Scenes

1. **Reading Maps**: The tool reads your KML file and understands:
   - Place names
   - Coordinates (latitude/longitude)
   - Any extra information you've added in Google Earth

2. **Smart Searching**: 
   - Creates smart search queries based on place names and context
   - Uses location coordinates to find more relevant results
   - Handles search service limits gracefully

3. **Saving Results**:
   - Saves search results in `search_cache.json`
   - Next time you search for the same place, it uses the saved results
   - Use `--bust-cache` when you want fresh results

4. **Usage Tracking**:
   - Keeps track of searches in `api_usage.log`
   - Helps you monitor your SerpAPI usage
   - Logs include timestamps and search details

## Files You'll See

- `search_cache.json`: Saved search results
- `contract_cache.json`: Saved contract search results
- `api_usage.log`: Record of all searches made
- `.env`: Your private API key (never share this!)

## Troubleshooting

1. **"API Key not found"**: Make sure you've created the `.env` file with your SerpAPI key
2. **"File not found"**: Check that your KML file name and path are correct
3. **Search limits**: If you hit search limits, the tool will wait and retry automatically

## Privacy & Data

- Your API key is kept private in the `.env` file
- Search results are saved locally on your computer
- Usage logs are stored only on your computer

## Need Help?

- Check the logs in `api_usage.log` to see what searches were made
- Use `--debug` to see more detailed information about what's happening
- Feel free to open an issue on GitHub if you need assistance

## Contributing

We welcome contributions! If you have ideas for improvements:
1. Fork the repository
2. Make your changes
3. Submit a pull request

## License

This project is licensed under the MIT License - feel free to use it for your own projects!

## Future Enhancements Under Consideration

1. **Contract Award Integration**:
   - Integration with government contract databases (e.g., USAspending.gov)
   - Historical contract award analysis by location
   - Spending pattern visualization

2. **Extended Data Sources**:
   - Historical satellite imagery analysis
   - Public records database integration
   - Environmental impact report correlation
   - Patent database geographic analysis

3. **Analysis Tools**:
   - Temporal analysis of activities by location
   - Geographic clustering analysis
   - Network relationship mapping
   - Data visualization and reporting

4. **Research Collaboration**:
   - Structured data export for academic analysis
   - Citation management
   - Collaborative research notes
   - Findings documentation system

## Academic Use

When using this tool for research:
1. **Data Verification**: Always verify findings through multiple sources
2. **Documentation**: Keep detailed records of search parameters and results
3. **Ethics**: Ensure compliance with academic research ethics guidelines
4. **Privacy**: Respect privacy considerations when handling location data
5. **Citations**: Properly cite all sources in academic publications 