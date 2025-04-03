import os
import easy_bible_format.converters.sword_to_ebf

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
                output_filename = os.path.splitext(filename)[0] + '.json'
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

def main():
    scan_and_convert("rawzip", "ebf")

if __name__ == "__main__":
    main()