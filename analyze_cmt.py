import csv
import subprocess
import json
import argparse

mdt_list = []
# Define the limit map for each field type
limit_map = {
    'string': ['length', 250],
    'double': ['precision', 10]
    # Add more types and their limits as needed
}

results_map = {}
results_of_queries = []


def sObject_get_describe(sObject):
    """
    This method retrieves and parses the metadata information of a Salesforce sObject using the Salesforce CLI.
    It runs the 'sobject describe' command, parses the JSON response, and extracts relevant field information
    for custom fields that exceed certain limits defined in 'limit_map'.

    Args:
        sObject (str): The name of the Salesforce object (sObject) to describe.

    Returns:
        tuple: A tuple containing the name of the sObject and a list of dictionaries with field information
               (name, length, type, digits, precision, extraTypeInfo) for fields that exceed defined limits.
               Returns an empty list if the command fails.
    """

    # Run the command using subprocess and capture the output
    command = ["sf", "sobject", "describe", "--sobject", sObject]
    try:
        print(f"Getting all needed information for: {sObject}")
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output = result.stdout

        # Parse the JSON output
        data = json.loads(output)
        # Extract the name attribute from the top-level JSON object
        top_level_name = data.get('name')

        # Extract relevant information from each field in the fields array
        field_information = []
        for field in data.get('fields', []):
            if field.get('custom') is True and field.get('type') in limit_map:
                field_type = field.get('type')
                field_for_length = limit_map.get(field_type)[0]

                field_length = field.get(field_for_length)
                if field_length > limit_map.get(field_type)[1]:
                    field_info = {
                        'name': field.get('name'),
                        'length': field.get('length'),
                        'type': field.get('type'),
                        'digits': field.get('type'),
                        'precision': field.get('precision'),
                        'extraTypeInfo': field.get('extraTypeInfo')
                    }
                    field_information.append(field_info)

        return top_level_name, field_information

    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e.stderr}")
        return []


def get_all_objects_from_org():
    """
    This method retrieves all custom objects from a Salesforce organization using the Salesforce CLI.
    It runs the 'org list metadata' command to get metadata related to CustomObjects in JSON format.

    Returns:
        dict: The parsed JSON response containing metadata about CustomObjects if the command succeeds,
              or an empty list if the command fails or the status is not 0 (indicating failure).
    """

    # Run the command using subprocess and capture the output
    command = ["sf", "org", "list", "metadata", "--json", "--metadata-type", "CustomObject"]
    try:
        print(f"Querying all Custom Objects from Org...")
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output = result.stdout

        # Parse the JSON output
        data = json.loads(output)

        # Check if the status is 0 (indicating success)
        if data.get('status') != 0:
            print(f"Command failed with status: {data.get('status')}")
            return []

        return data

    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e.stderr}")
        return []


def filter_cmdt_out(json):
    """
    This method filters Custom Metadata Types (CMDT) from a given JSON input.
    It extracts the 'fullName' of records that have a suffix of '__mdt', which
    is the standard naming convention for Custom Metadata Types in Salesforce.

    Args:
        json (dict): The JSON object containing metadata records.

    Returns:
        list: A list of 'fullName' values for all Custom Metadata Types found in the input JSON.
    """

    print("Filtering Custom Metadata Types")
    mdt_full_names = [record['fullName'] for record in json.get('result', []) if record.get('fullName', '').endswith('__mdt')]
    return mdt_full_names


def write_dict_to_csv(data, filename):
    """
    This method writes a dictionary of field statistics to a CSV file. The dictionary contains object types
    as keys and each object contains another dictionary with field names and their associated statistics 
    (such as the longest, shortest, and count of values).

    Args:
        data (dict): A dictionary where each key is an object type, and the value is another dictionary containing
                     field names as keys and 'longest', 'shortest', and 'count' keys with corresponding statistics.
        filename (str): The name of the CSV file to which the data will be written.

    Writes:
        A CSV file with the following headers: 'Object', 'Field', 'Longest', 'Shortest', 'Count'.
        Each row in the CSV represents a field and its corresponding statistics under a specific object type.
    """

    # Define the header based on the new structure
    headers = ['Object', 'Field', 'Longest', 'Shortest', 'Count', 'Type Info']

    # Open the file for writing
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)

        # Write the header
        writer.writerow(headers)

        # Iterate over the objects in the data
        for cmd_name, fields in data.items():
            # Iterate over each field in the object's field dictionary
            for field, stats in fields.items():
                row = [
                    cmd_name,               # Object name (cmd_name)
                    field,                  # Field name
                    stats['longest'],       # Longest value
                    stats['shortest'],      # Shortest value
                    stats['count'],         # Count of occurrences
                    stats['extraTypeInfo']  # Type of field
                ]
                writer.writerow(row)


def generate_sf_queries(results_map):
    """
    Generates Salesforce CLI queries for metadata types with fields.

    Args:
        results_map (dict): A dictionary where keys are metadata types (res) and values are lists of field info.

    Returns:
        list: A list of Salesforce CLI query strings.
    """
    queries = []
    print("Generating all queries.")
    for mdt, fields in results_map.items():
        if fields:  # Only generate queries for metadata types with fields
            field_names = ", ".join(field.get('name') for field in fields if field.get('name'))
            query = f'sf data query --json --query "SELECT {field_names} FROM {mdt}"'
            queries.append(query)

    return queries


def execute_query(query):
    """
    This method executes a given command-line query using the subprocess module and captures its output.
    The output is expected to be in JSON format, which is then parsed and returned.

    Args:
        query (str): The command-line query to execute.

    Returns:
        dict or None: If the query output is successfully parsed as JSON, the result is returned as a dictionary.
                      If the parsing fails, it returns None and logs an error message.
    """

    # print(f"Executing query: {query}")
    process = subprocess.run(query, shell=True, capture_output=True, text=True)

    try:
        result = json.loads(process.stdout)  # Parse the JSON output
        return result
    except json.JSONDecodeError:
        print(f"Failed to parse JSON from query output: {process.stdout}")
        return None



def analyze_field_lengths(query_results, results_map):
    """
    Analyzes the lengths of field values in query results and updates statistics for each field.
    
    Args:
        query_results (list): A list of dictionaries containing the results of Salesforce queries.
        results_map (dict): A dictionary mapping each object (cmd_name) to a list of field metadata.
                            This includes field names, types, lengths, and extra type information.

    Returns:
        dict: A dictionary (stats) where each key is an object (cmd_name), and the value is another
              dictionary containing statistics for each field in that object. Each field has statistics 
              for 'longest', 'shortest', 'count' (number of occurrences), 'field_length' (the defined length 
              or precision of the field), and 'extraTypeInfo' (e.g., Lookup or TextArea).
    """
    stats = {}

    for result in query_results:
        if 'result' not in result or 'records' not in result['result']:
            print(f"Invalid result format: {result}")
            continue

        records = result['result']['records']

        for record in records:
            # Extract the 'type' from 'attributes' if it exists
            if 'attributes' in record and 'type' in record['attributes']:
                cmd_name = record['attributes']['type']
            else:
                cmd_name = "Unknown"  # Fallback if type isn't available

            # Initialize stats for this object type if it doesn't exist yet
            if cmd_name not in stats:
                stats[cmd_name] = {}

            # Process each field in the record
            for field, value in record.items():
                if field == "attributes":
                    continue

                all_fields = results_map.get(cmd_name, [])
                current_field_length = 0
                extraTypeInfo = ''
                # Check for the field in the results_map to get the defined length
                for field_n in all_fields:
                    if field_n['name'] == field:
                        if field_n['extraTypeInfo'] == 'externallookup':
                            extraTypeInfo = 'Lookup'
                        elif field_n['extraTypeInfo'] == 'plaintextarea':
                            extraTypeInfo = 'TextArea'

                        if field_n['type'] == 'string':
                            current_field_length = field_n['length']
                        elif field_n['type'] == 'double':
                            current_field_length = field_n['precision']
                        break

                value_length = len(str(value)) if value is not None else 0

                # Initialize field stats if it's the first time encountering this field
                if field not in stats[cmd_name]:
                    stats[cmd_name][field] = {
                        'longest': value_length,
                        'shortest': value_length,
                        'count': 1,
                        'field_length': current_field_length,
                        'extraTypeInfo': extraTypeInfo
                    }
                else:
                    # Update the stats for this field
                    stats[cmd_name][field]['longest'] = max(stats[cmd_name][field]['longest'], value_length)
                    stats[cmd_name][field]['shortest'] = min(stats[cmd_name][field]['shortest'], value_length)
                    stats[cmd_name][field]['count'] += 1

    return stats


def print_markdown_table(stats):
    """
    This method prints a Markdown-formatted table displaying field statistics.
    The table includes columns for object names, field names, longest values, shortest values, 
    field lengths, and counts.

    Args:
        stats (dict): A dictionary where each key is an object type, and the value is another dictionary 
                      containing field names as keys, and each field has 'longest', 'shortest', 'field_length', 
                      and 'count' keys with corresponding statistics.

    Prints:
        A Markdown table with headers and rows formatted based on the field statistics provided.
    """

    # Define the headers
    headers = ["Object", "Field", "Longest", "Shortest", "Length", "Count" , "Type Info"]

    # Create the header line with specified widths
    header_line = f"|{headers[0]:<60} | {headers[1]:<50} | {headers[2]:<10} | {headers[3]:<10} | {headers[4]:<10} | {headers[5]:<6} | {headers[6]:<10}"

    # Create the separator line based on the length of the header line
    separator = "-" * len(header_line)

    # Initialize the markdown table with the header and separator
    markdown_table = header_line + "\n" + separator + "\n"

    # Iterate over the object types in the stats dictionary
    for cmd_name, fields in stats.items():
        # Iterate over each field in the object's field dictionary
        for field, attributes in fields.items():
            markdown_table += f"|{cmd_name:<60} | {field:<50} | {attributes['longest']:<10} | {attributes['shortest']:<10} | {attributes['field_length']:<10} | {attributes['count']:<6} | {attributes['extraTypeInfo']:<10}\n"

        markdown_table += separator + "\n"
    # Print the markdown table
    print(markdown_table)


def main():
    """
    Main function to process metadata types in the Salesforce organization.
    It handles different command-line arguments to either fetch metadata types,
    process a provided list, and output results as a CSV file or Markdown table.

    Command-line Arguments:
        -f: Fetch all objects from the org and filter for custom metadata types.
        -l: Specify a list of custom metadata types directly.
        -c: Write the results to a CSV file instead of printing.
        -o: Specify the name of the CSV file to write to. Defaults to 'output.csv'.
        -m: Print the results as a Markdown table.

    Process:
        1. Fetch or use provided list of Custom Metadata Types.
        2. Describe each Custom Metadata Type.
        3. Generate queries for each type and execute them.
        4. Analyze and sort the results.
        5. Output the results based on user preferences.
    """

    parser = argparse.ArgumentParser(description="Process metadata types in the org.")
    parser.add_argument("-f", action="store_true", help="Fetch all objects from the org and filter for custom metadata types.")
    parser.add_argument("-l", nargs='+', help="Specify a list of custom metadata types directly.")
    parser.add_argument("-c", action="store_true", help="If specified, the results will be written to a CSV file instead of printed.")
    parser.add_argument("-o", type=str, default="output.csv", help="Name of the CSV file to write to. Defaults to 'output.csv'.")
    parser.add_argument("-m", action="store_true", help="Print the results as a markdown table.")

    args = parser.parse_args()

    if args.f:
        # Get all Custom Metadata Types in the Org
        all_objects = get_all_objects_from_org()
        mdt_list = filter_cmdt_out(all_objects)
        print(f"MDT List from org: {mdt_list}")

    elif args.l:
        # User provided the list directly
        mdt_list = args.l
        print(f"MDT List provided by user: {mdt_list}")

    else:
        print("Please specify either -f or -l with appropriate arguments.")
        return

    # Initialize results map and list
    results_map = {}
    results_of_queries = []

    # Get descriptions for each Custom Metadata Type
    for sObject_name in mdt_list:
        res, fields = sObject_get_describe(sObject_name)
        # Store the results in the results_map dictionary
        results_map[res] = fields

    # Generate and execute queries for each Custom Metadata Type
    queries = generate_sf_queries(results_map)
    for query in queries:
        result = execute_query(query)
        if result is not None:
            results_of_queries.append(result)

    # Sort results by totalSize in descending order
    sorted_results = sorted(results_of_queries, key=lambda x: x['result']['totalSize'], reverse=True)

    # Analyze field lengths and get statistics
    field_stats = analyze_field_lengths(sorted_results, results_map)

    # Output results based on user preferences
    if args.c:
        write_dict_to_csv(field_stats, args.o)
    if args.m:
        print_markdown_table(field_stats)

    # Default behavior is to print the field stats if no other option is specified
    if not args.c and not args.m:
        print("Field Stats:", field_stats)


if __name__ == "__main__":
    main()
