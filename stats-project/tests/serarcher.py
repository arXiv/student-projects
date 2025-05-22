import os

def find_test_data(filename="test_download_data.json", search_path="."):
    print(f"🔍 Searching for '{filename}' in '{search_path}' and subdirectories...\n")

    for root, _, files in os.walk(search_path):
        if filename in files:
            file_path = os.path.join(root, filename)
            print(f"✅ Found: {file_path}")
            return file_path  # Return the first match

    print("❌ File not found.")
    return None

# Define the search path starting from 'stats-project/tests/test_data'
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Get the absolute path to the project root
search_directory = os.path.join(project_root, "tests", "test_data")  # Build the path to the test_data folder

# Run the search
file_path = find_test_data("test_download_data.json", search_directory)
