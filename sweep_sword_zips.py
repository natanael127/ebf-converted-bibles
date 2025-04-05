import os
import tempfile
import requests
from bs4 import BeautifulSoup
import time
import shutil
import easy_bible_format.converters.sword_to_ebf
import argparse

LOG_FILE = "sword_conversion.log"

def scan_and_convert(input_dir, output_dir=None):
    """
    Scan a directory for SWORD modules and convert them to JSON format
    
    Args:
        input_dir (str): Directory containing SWORD modules
        output_dir (str, optional): Directory where JSON files will be saved
    """
    if not output_dir:
        output_dir = input_dir
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Track conversion statistics
    processed = 0
    errors = 0
    
    for root, _, files in os.walk(input_dir):
        for filename in files:
            # Look for typical SWORD module files (zip, imp, or no extension)
            if filename.endswith('.zip') or filename.endswith('.imp') or '.' not in filename:
                input_path = os.path.join(root, filename)
                output_filename = os.path.splitext(filename)[0] + '.ebf1.json'
                output_path = os.path.join(output_dir, output_filename)
                
                try:
                    print(f"Converting {input_path} to {output_path}...")
                    easy_bible_format.converters.sword_to_ebf.converter(input_path, output_path)
                    processed += 1
                except Exception as e:
                    with open(LOG_FILE, 'a') as log_file:
                        log_file.write(f"Error converting {input_path}: {str(e)}\n")
                    errors += 1
    
    print(f"\nConversion complete. Processed {processed} files with {errors} errors.")

def scan_and_convert_web(url, output_dir, skip_existing=True):
    """
    Scan a web directory for SWORD modules and convert them to JSON format
    
    Args:
        url (str): URL of the directory containing SWORD modules
        output_dir (str): Directory where JSON files will be saved
        skip_existing (bool): Skip files that already exist in output directory
        delay (float): Delay between downloads in seconds
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Track conversion statistics
    processed = 0
    errors = 0
    skipped = 0
    already_exists = 0
    
    # Create a temporary directory for downloads
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Get the directory listing
        print(f"Fetching directory listing from {url}...")
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all links
        links = soup.find_all('a')
        
        # Filter links to get only zip files
        zip_files = []
        for link in links:
            href = link.get('href', '')
            if href.endswith('.zip') and not href.startswith('..'):
                zip_files.append(href.split('?')[0])
        
        total_files = len(zip_files)
        print(f"Found {total_files} zip files")
        
        # Process each zip file
        for i, filename in enumerate(zip_files, 1):
            safe_filename = os.path.basename(filename)
            
            # Check if output already exists
            output_filename = os.path.splitext(safe_filename)[0] + '.ebf1.json'
            output_path = os.path.join(output_dir, output_filename)
            
            if skip_existing and os.path.exists(output_path):
                print(f"Skipping {safe_filename} (output file already exists)")
                already_exists += 1
                continue
            
            # Construct the full URL
            if url.endswith('/') and filename.startswith('/'):
                file_url = url[:-1] + filename
            elif url.endswith('/') or filename.startswith('/'):
                file_url = url + filename
            else:
                file_url = url + '/' + filename
                
            print(f"Processing {i}/{total_files}: {safe_filename}")
            
            # Download the file
            try:
                download_path = os.path.join(temp_dir, safe_filename)
                print(f"Downloading {file_url} to {download_path}...")

                download_response = requests.get(file_url, stream=True)
                download_response.raise_for_status()
                
                with open(download_path, 'wb') as f:
                    for chunk in download_response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # Process the downloaded file
                try:
                    print(f"Converting {download_path} to {output_path}...")
                    easy_bible_format.converters.sword_to_ebf.converter(download_path, output_path)
                    processed += 1
                except Exception as e:
                    with open(LOG_FILE, 'a') as log_file:
                        log_file.write(f"Error converting {download_path}: {str(e)}\n")
                    errors += 1
                
                # Clean up the downloaded file
                os.remove(download_path)
                
            except Exception as e:
                with open(LOG_FILE, 'a') as log_file:
                    log_file.write(f"Error downloading {file_url}: {str(e)}\n")
                skipped += 1
                
    finally:
        # Clean up the temporary directory
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
    
    print(f"\nConversion complete:")
    print(f"  - Processed: {processed} files")
    print(f"  - Errors: {errors} files")
    print(f"  - Skipped (download errors): {skipped} files")
    print(f"  - Already exists: {already_exists} files")

def main():
    parser = argparse.ArgumentParser(description='Convert SWORD Bible modules to JSON format.')
    parser.add_argument('--force', action='store_true', 
                        help='Force processing even if output file already exists')
    parser.add_argument('--url', default="https://www.crosswire.org/ftpmirror/pub/sword/packages/rawzip/",
                        help='URL to scan for SWORD modules')
    parser.add_argument('--output', default="crosswire",
                        help='Output directory for converted files')
    args = parser.parse_args()
    
    scan_and_convert_web(args.url, args.output, skip_existing=not args.force)

if __name__ == "__main__":
    main()
