## Dependencies

The script relies on the following Python packages:

- Python 3.7 or higher
- [spaCy](https://spacy.io/) (`en_core_web_lg` model)
- `requests`
- `pandas`
- `tqdm`
- `tenacity`
- `concurrent.futures` (Standard library in Python 3)
- `argparse`
- `json`
- `glob`
- `logging`

## Usage

Run the script using the command line: (example)

```
python ORG_extraction.py --dataset /dataset/2201_samp --output_excel results.xlsx --output_json results.json  --workers 4 --ground_truth_dir /dataset/2201_samp_test_set
```

### Command-Line Arguments

- `--dataset`: **(Required)** Path to the dataset directory containing the `.tar.gz` archives of LaTeX files.
- `--ground_truth_dir`: **(Required)** Path to the ground truth data directory containing JSON files.
- `--output_excel`: Path to the output Excel file. Default is `organization_extraction_results.xlsx`.
- `--output_json`: Path to the output JSON file. Default is `organization_extraction_results.json`.
- `--limit`: Limit on the number of files to process. Default is `None` (process all files).
- `--workers`: Number of parallel worker threads. Default is `4`.

## Output Files

### Excel File (`.xlsx`)

The Excel file contains a table with the following columns:

- `Archive`: Name of the processed archive file.
- `Organization`: Extracted organization name.
- `ROR_ID`: ROR identifier of the organization.
- `ROR_Name`: Standardized organization name from ROR.
- `Country`: Country where the organization is based.
- `Type`: Type(s) of the organization.

### JSON File (`.json`)

The JSON file provides a structured output with the following format:

```
json复制代码[
  {
    "Archive": "archive_name.tar.gz",
    "Organizations": [
      {
        "Organization": "Organization Name",
        "ROR_ID": "https://ror.org/xxxxx",
        "ROR_Name": "Standardized Organization Name",
        "Country": "Country Name",
        "Type": "Type of Organization"
      },
      ...
    ]
  },
  ...
]
```

## Logging

The script generates a log file named `organization_extraction.log`, which contains detailed information about the execution, including:

- Status of archive extraction.
- ROR API query results.
- Matching and non-matching organization names.
- Errors and warnings.

## Performance Metrics

After processing, the script outputs overall accuracy metrics:

- **Precision**: The proportion of correctly identified organizations out of all organizations identified.
- **Recall**: The proportion of correctly identified organizations out of all actual organizations.
- **F1-Score**: The harmonic mean of precision and recall.

These metrics are also logged in the log file.

## How It Works

1. **Archive Processing**:
   - The script searches for `.tar.gz` files in the dataset directory.
   - Extracts each archive into a temporary directory.
   - Searches for LaTeX (`.tex`) files, prioritizing `main.tex`.
2. **Text Extraction and Cleaning**:
   - Reads the content before the `\begin{abstract}` section in the LaTeX files.
   - Cleans the text by removing LaTeX commands, mathematical formulas, and special characters.
3. **Organization Extraction**:
   - Uses spaCy's NLP model to identify entities labeled as `ORG` (organizations).
4. **ROR Querying and Caching**:
   - For each extracted organization, queries the ROR API to obtain standardized information.
   - Utilizes a caching mechanism (`ror_cache.json`) to store ROR query results and minimize API calls.
5. **Ground Truth Comparison**:
   - Matches extracted organizations with ground truth affiliations from corresponding JSON files.
   - Calculates true positives (TP), false positives (FP), and false negatives (FN).
6. **Metrics Calculation**:
   - Computes precision, recall, and F1-score for each archive and overall.
7. **Results Compilation**:
   - Saves the results in Excel and JSON formats.
   - Logs detailed processing information.