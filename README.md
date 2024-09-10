# Salesforce Custom Metadata Analyzer

This script is designed to analyze your Salesforce Custome Metadata. It retrieves metadata information, generates queries, executes them, and outputs field statistics either to a CSV file or as a Markdown table.

## Features

- **Fetch Metadata:** Retrieve all Custom Metadata Types from a Salesforce organization.
- **Direct Input:** Specify a list of Custom Metadata Types directly.
- **Output Options:** Write results to a CSV file or print them as a Markdown table.
- **Field Analysis:** Analyze field lengths and provide statistics on the fields.

## Requirements

- Salesforce CLI (`sf`) installed and configured.
- Python 3.x with the `subprocess`, `json`, `csv`, and `argparse` modules.

## Installation

1. Clone this repository:
   ```sh
   git clone https://github.com/yourusername/salesforce-metadata-analyzer.git
