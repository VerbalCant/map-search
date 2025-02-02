# Location Search Tool

A research tool designed to gather and analyze publicly available information about locations of interest. Part of an open source transparency effort to understand relationships between different geographical locations and their potential significance.

## Purpose

This tool helps researchers investigate locations by automatically collecting and analyzing:
1. Public information from web searches about each location
2. Government contract data related to activities in these areas

## Current Capabilities

### Location Information Search
- Takes a set of locations from a KML file (e.g., from Google Earth)
- Performs intelligent geographic-aware web searches
- Collects and organizes relevant information about each location
- Caches results for future reference

Example web search findings:
```json
{
  "location_example": [
    {
      "title": "Dog Bone Lake (Nevada)",
      "link": "https://en.wikipedia.org/wiki/Dog_Bone_Lake_(Nevada)",
      "body": "Dog Bone Lake is a dog bone-shaped topographic flat with two larger ends connected by a narrow body..."
    }
  ]
}
```

### Government Contract Analysis
- Searches USAspending.gov data for contracts in each location
- Analyzes contract values, recipients, and descriptions
- Identifies patterns in government spending and activities

Example contract findings:
```
Found contracts worth $27,066,632,618.55 in the area
Top Contractors:
  - MISSION SUPPORT & TEST SERVICES LLC: $6.1B
  - NATIONAL SECURITY TECHNOLOGIES, LLC: $5.6B
  - SIERRA NEVADA COMPANY, LLC: $3.8B
```

Example contract details:
```json
{
  "location_example": [
    {
      "Award ID": "DENA0003624",
      "Recipient Name": "MISSION SUPPORT & TEST SERVICES LLC",
      "Award Amount": 6096331200.02,
      "Description": "CONTRACT AWARD FOR THE MANAGEMENT AND OPERATION OF THE DEPARTMENT OF ENERGY NATIONAL NUCLEAR SECURITY ADMINISTRATION'S NEVADA NATIONAL SECURITY SITE",
      "Awarding Agency": "Department of Energy",
      "Funding Agency": "Department of Defense"
    }
  ]
}
```

## Basic Usage

```bash
python location_analyzer.py --kml-file your_locations.kml
```

## Getting Started

1. Clone this repository
2. Create a Python virtual environment and install requirements
3. Get a SerpAPI key for web searches
4. Run the tool with your KML file

For detailed setup instructions, see SETUP.md

## Future Plans

- Pattern analysis across locations
- Additional data source integration
- Relationship mapping between locations
- Historical data analysis
- Automated report generation

## Contributing

This is an open source project aimed at improving transparency through data analysis. Contributions are welcome! 