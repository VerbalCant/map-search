# Location Search Tool

This tool helps you discover information about places marked in Google Earth (KML) files. Think of it as a smart assistant that reads your map markers and finds relevant information about each location on the internet.

## What Does It Do?

1. **Reads Your Map Data**: Takes KML files (the kind you export from Google Earth) and understands the places you've marked
2. **Finds Information**: Searches the internet for each location to find relevant articles, websites, and information
3. **Saves Time**: Remembers what it found before so you don't have to search for the same places twice
4. **Tracks Usage**: Keeps track of how many searches you've made to help manage your search service costs

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

Examples:
```bash
# Process just 3 places
python location_analyzer.py --max-places 3

# Get fresh results (ignore cached data)
python location_analyzer.py --bust-cache

# Get more search results per location
python location_analyzer.py --max-results 10
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