import os
import tarfile
import tempfile
import re
import spacy
import requests
import pandas as pd
from tqdm import tqdm
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import json
from tenacity import retry, stop_after_attempt, wait_fixed
import glob

# Configure logging
logging.basicConfig(
    filename='organization_extraction.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize spaCy model (choose language model as needed)
nlp = spacy.load("en_core_web_lg")

# Configure ROR API information
ROR_SEARCH_URL = 'https://api.ror.org/organizations'

# Initialize ROR cache
ror_cache = {}

# Load persistent cache
cache_file = 'ror_cache.json'
if os.path.exists(cache_file):
    with open(cache_file, 'r', encoding='utf-8') as f:
        ror_cache = json.load(f)
    logging.info("Loaded persistent ROR cache.")
else:
    logging.info("No persistent ROR cache found. Using empty cache.")

@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
def query_ror(institution_name):
    """
    Query ROR information, returning details only if the name exactly matches.
    """
    if institution_name in ror_cache:
        return ror_cache[institution_name]
    
    # ROR API search endpoint
    search_url = ROR_SEARCH_URL
    params = {'query': institution_name}
    
    try:
        response = requests.get(search_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('items'):
                # Iterate through all returned items to find an exact name match
                for item in data['items']:
                    ror_name = item.get('name', '').strip()
                    # Compare names, case-insensitive and ignore leading/trailing spaces
                    if ror_name.lower() == institution_name.strip().lower():
                        ror_cache[institution_name] = {
                            'ROR_ID': item.get('id', 'N/A'),
                            'Name': ror_name,
                            'Country': item.get('country', {}).get('country_name', 'N/A'),
                            'Type': ', '.join(item.get('types', []))
                        }
                        logging.info(f"Found ROR ID for '{institution_name}': {item.get('id', 'N/A')}")
                        return ror_cache[institution_name]
                
                # If no exact match found
                logging.warning(f"No exact match found for institution '{institution_name}' in ROR.")
                ror_cache[institution_name] = None
                return None
            else:
                logging.warning(f"No ROR information found for institution '{institution_name}'.")
                ror_cache[institution_name] = None
                return None
        else:
            logging.error(f"ROR API query failed with status code: {response.status_code} for institution: {institution_name}")
            ror_cache[institution_name] = None
            return None
    except Exception as e:
        logging.error(f"ROR API query exception for institution: {institution_name}, Error: {e}")
        ror_cache[institution_name] = None
        return None

def extract_tar_gz(tar_path, extract_path):
    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=extract_path)
        logging.info(f"Successfully extracted: {tar_path}")
    except Exception as e:
        logging.error(f"Failed to extract: {tar_path}, Error: {e}")

def find_tex_files(extracted_dir):
    main_tex = None
    tex_files = []
    for root, dirs, files in os.walk(extracted_dir):
        for file in files:
            if file.endswith(".tex"):
                if file.lower() == "main.tex":
                    main_tex = os.path.join(root, file)
                    break
                else:
                    tex_files.append(os.path.join(root, file))
        if main_tex:
            break
    if main_tex:
        return [main_tex]
    else:
        return tex_files

def clean_text(text):
    """
    Clean the text by removing LaTeX commands, mathematical formulas, braces, newlines, and extra spaces.
    """
    # Remove LaTeX commands like \command{...}
    text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', text)
    text = re.sub(r'\\[a-zA-Z]+\[[^\]]*\]\{[^}]*\}', '', text)
    # Remove mathematical formulas like $...$
    text = re.sub(r'\$[^$]*\$', '', text)
    # Remove braces and newlines
    text = text.replace('{', '').replace('}', '').replace('\n', ' ')
    # Remove extra spaces
    text = ' '.join(text.split())
    return text.strip()

def extract_content_before_abstract(tex_path):
    try:
        with open(tex_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Use regex to find \begin{abstract}
        match = re.search(r'\\begin\{abstract\}', content, re.IGNORECASE)
        if match:
            content_before_abstract = content[:match.start()]
        else:
            content_before_abstract = content
        # Clean the text
        cleaned_text = clean_text(content_before_abstract)
        return cleaned_text
    except Exception as e:
        logging.error(f"Failed to read file: {tex_path}, Error: {e}")
        return ""

def extract_organizations(text):
    doc = nlp(text)
    orgs = set()
    for ent in doc.ents:
        if ent.label_ == "ORG":
            orgs.add(ent.text.strip())
    return list(orgs)

def get_main_identifier(archive_filename):
    """
    Extract the main identifier from the archive filename, e.g., '2201.00001'.
    """
    match = re.match(r'^(\d+\.\d+)', archive_filename)
    if match:
        return match.group(1)
    else:
        return None

def find_ground_truth_file(main_id, ground_truth_dir):
    """
    Find the corresponding ground truth JSON file based on the main identifier.
    """
    pattern = os.path.join(ground_truth_dir, f"{main_id}*.json")
    matching_files = glob.glob(pattern)
    if matching_files:
        return matching_files[0]  # Assuming only one match
    else:
        return None

def extract_affiliations_from_ground_truth(gt_file):
    """
    Extract all unique organization names (Affiliations) from the ground truth file.
    """
    with open(gt_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    affiliations = set()
    for person, details in data.items():
        affil = details.get('Affiliation', [])
        affiliations.update([a.strip().lower() for a in affil])
    return affiliations

def process_archive(tar_path, ground_truth_dir):
    """
    Process a single archive file, extract organizations, and compare with ground truth.
    """
    organizations = {}
    ground_truth_affiliations = set()
    archive_name = os.path.basename(tar_path)
    main_id = get_main_identifier(archive_name)
    
    if main_id:
        gt_file = find_ground_truth_file(main_id, ground_truth_dir)
        if gt_file:
            ground_truth_affiliations = extract_affiliations_from_ground_truth(gt_file)
            logging.info(f"Loaded ground truth file: {gt_file}")
        else:
            logging.warning(f"No ground truth file found for archive '{archive_name}'.")
    else:
        logging.warning(f"Could not extract main identifier from archive filename: {archive_name}")
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            extract_tar_gz(tar_path, tmpdir)
            tex_files = find_tex_files(tmpdir)
            if not tex_files:
                logging.warning(f"No .tex files found in archive: {tar_path}")
                return organizations, ground_truth_affiliations
            for tex_file in tex_files:
                content = extract_content_before_abstract(tex_file)
                if not content:
                    continue
                orgs = extract_organizations(content)
                for org in orgs:
                    if org not in organizations:
                        ror_info = query_ror(org)
                        if ror_info and ror_info['Name'].lower() == org.lower():
                            organizations[org] = ror_info
    except Exception as e:
        logging.error(f"Exception while processing archive: {tar_path}, Error: {e}")
    return organizations, ground_truth_affiliations

def main(dataset_dir, ground_truth_dir, output_excel, output_json, max_workers=4, file_limit=None):
    all_results = []
    
    # Collect all .tar.gz files
    tar_files = []
    for root, dirs, files in os.walk(dataset_dir):
        for file in files:
            if file.endswith(".tar.gz"):
                tar_files.append(os.path.join(root, file))
    
    # Apply file limit if set
    if file_limit is not None:
        tar_files = tar_files[:file_limit]
        logging.info(f"File processing limit set: Processing the first {file_limit} files.")
    
    # Initialize metrics
    total_tp = 0
    total_fp = 0
    total_fn = 0
    
    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all archive processing tasks
        future_to_tar = {executor.submit(process_archive, tar, ground_truth_dir): tar for tar in tar_files}
        # Use tqdm to display progress
        for future in tqdm(as_completed(future_to_tar), total=len(tar_files), desc="Processing archives", unit="archive"):
            tar_path = future_to_tar[future]
            try:
                organizations, ground_truth_affiliations = future.result()
                archive_name = os.path.basename(tar_path)
                extracted_orgs = set([org.lower() for org in organizations.keys()])
                
                # Calculate metrics
                tp = len(extracted_orgs.intersection(ground_truth_affiliations))
                fp = len(extracted_orgs - ground_truth_affiliations)
                fn = len(ground_truth_affiliations - extracted_orgs)
                
                total_tp += tp
                total_fp += fp
                total_fn += fn
                
                precision = tp / (tp + fp) if (tp + fp) > 0 else 0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0
                f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
                
                logging.info(f"Archive '{archive_name}' - TP: {tp}, FP: {fp}, FN: {fn}, Precision: {precision:.2f}, Recall: {recall:.2f}, F1: {f1:.2f}")
                
                # Organize JSON structure
                if organizations:
                    org_list = []
                    for org, ror_info in organizations.items():
                        org_entry = {
                            "Organization": org,
                            "ROR_ID": ror_info.get('ROR_ID', 'N/A'),
                            "ROR_Name": ror_info.get('Name', 'N/A'),
                            "Country": ror_info.get('Country', 'N/A'),
                            "Type": ror_info.get('Type', 'N/A')
                        }
                        org_list.append(org_entry)
                    all_results.append({
                        "Archive": archive_name,
                        "Organizations": org_list
                    })
                else:
                    all_results.append({
                        "Archive": archive_name,
                        "Organizations": []
                    })
            except Exception as e:
                logging.error(f"Failed to process archive: {tar_path}, Error: {e}")
    
    # Save to Excel
    excel_records = []
    for entry in all_results:
        archive = entry["Archive"]
        if entry["Organizations"]:
            for org in entry["Organizations"]:
                excel_records.append({
                    "Archive": archive,
                    "Organization": org.get("Organization", "N/A"),
                    "ROR_ID": org.get("ROR_ID", "N/A"),
                    "ROR_Name": org.get("ROR_Name", "N/A"),
                    "Country": org.get("Country", "N/A"),
                    "Type": org.get("Type", "N/A")
                })
    if excel_records:
        df_excel = pd.DataFrame(excel_records)
        try:
            df_excel.to_excel(output_excel, index=False)
            logging.info(f"Results saved to Excel: {output_excel}")
            print(f"Excel results saved to: {output_excel}")
        except Exception as e:
            logging.error(f"Failed to save Excel file: {output_excel}, Error: {e}")
            print(f"Failed to save Excel file: {output_excel}, Error: {e}")
    else:
        logging.info("No matching organizations extracted. Excel file not generated.")
        print("No matching organizations extracted. Excel file not generated.")
    
    # Save to JSON
    try:
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=4)
        logging.info(f"Results saved to JSON: {output_json}")
        print(f"JSON results saved to: {output_json}")
    except Exception as e:
        logging.error(f"Failed to save JSON file: {output_json}, Error: {e}")
        print(f"Failed to save JSON file: {output_json}, Error: {e}")
    
    # Save cache
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(ror_cache, f, ensure_ascii=False, indent=4)
        logging.info("ROR cache saved.")
    except Exception as e:
        logging.error(f"Failed to save cache file: {cache_file}, Error: {e}")
    
    # Calculate and display overall accuracy
    overall_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    overall_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    overall_f1 = 2 * overall_precision * overall_recall / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0
    
    logging.info(f"Overall Accuracy - Precision: {overall_precision:.2f}, Recall: {overall_recall:.2f}, F1: {overall_f1:.2f}")
    print(f"Overall Accuracy - Precision: {overall_precision:.2f}, Recall: {overall_recall:.2f}, F1: {overall_f1:.2f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Organization Extraction Script")
    parser.add_argument('--dataset', type=str, required=True, help='Path to the dataset directory')
    parser.add_argument('--ground_truth_dir', type=str, required=True, help='Path to the ground truth data directory')
    parser.add_argument('--output_excel', type=str, default='organization_extraction_results.xlsx', help='Path to the output Excel file')
    parser.add_argument('--output_json', type=str, default='organization_extraction_results.json', help='Path to the output JSON file')
    parser.add_argument('--limit', type=int, default=None, help='Limit on the number of files to process')
    parser.add_argument('--workers', type=int, default=4, help='Number of parallel worker threads')
    
    args = parser.parse_args()
    
    main(args.dataset, args.ground_truth_dir, args.output_excel, args.output_json, max_workers=args.workers, file_limit=args.limit)
