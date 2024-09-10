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

## Usage

You can run the script with various command-line arguments to perform different tasks related to Salesforce metadata analysis.

### Command-Line Arguments

- `-f`: Fetch all objects from the org and filter for custom metadata types.
- `-l <list>`: Specify a list of custom metadata types directly. You can provide multiple types separated by spaces.
- `-c`: Write the results to a CSV file instead of printing to the console.
- `-o <filename>`: Specify the name of the CSV file to write to. Defaults to `output.csv`.
- `-m`: Print the results as a Markdown table.

### Running the Script

To run the script, use the following command pattern:

```sh
python analyze_cmt.py [options]
```

## Examples
```sh
python script.py -l MyCustomMetadataType1__mdt MyCustomMetadataType2__mdt
```

```sh
python analyze_cmt.py -f -m -c -o all_of_my_results.csv
```

```sh
python analyze_cmt.py -m -l My_Custom_Metadata_Type__mdt Yet_Another_Custom_Metdata_Type__mdt
```
