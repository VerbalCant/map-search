# Setup Instructions

## Requirements

1. Python 3.7 or higher
2. A SerpAPI key for web searches
3. A KML file with locations to analyze

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Configuration

### SerpAPI Setup

1. Go to [SerpAPI's website](https://serpapi.com/)
2. Sign up for an account
3. Get your API key from the dashboard
4. Create a `.env` file in the project root:
```bash
echo "SERPAPI_KEY=your_key_here" > .env
```

Note: SerpAPI offers:
- Free tier: 100 searches/month
- Paid plans: Starting from $50/month
- Pay-as-you-go options

## Command Line Options

```bash
python location_analyzer.py [OPTIONS]
```

Options:
- `--kml-file FILE`: KML file to analyze (default: "Imminent_Domain.kml")
- `--max-places N`: Limit analysis to N locations
- `--max-results N`: Maximum search results per location (default: 5)
- `--bust-cache`: Ignore cached results
- `--debug`: Show detailed debug information
- `--search-radius N`: Search radius in miles (default: 50)
- `--contracts-only`: Only analyze contracts (skip web search)

## Troubleshooting

1. **API Key Issues**
   - Verify your `.env` file exists and contains the correct key
   - Check SerpAPI dashboard for usage limits

2. **KML File Issues**
   - Ensure file path is correct
   - Verify KML file format is valid
   - Check file permissions

3. **Search Limits**
   - Use `--max-places` to limit locations processed
   - Enable caching to avoid redundant searches
   - Monitor `api_usage.log` for usage tracking 