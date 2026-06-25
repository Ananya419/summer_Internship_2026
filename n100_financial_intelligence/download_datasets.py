import os
import subprocess
import sys

# Define folder IDs from shared Google Drive links
CORE_FOLDER_ID = "1qpx7VTfTo46GMDQ_dR3ctYK2G6zKYE8-"
SUPPORTING_FOLDER_ID = "1yNTEbZMWKETbpUaZAeJjb3tPExyk8R_k"

dest_dir = r"C:\Users\sants\OneDrive\Desktop\Internship_2026\n100_financial_intelligence\data\raw"
os.makedirs(dest_dir, exist_ok=True)

print("Starting Google Drive folder downloads...")

# Download Core datasets
print("Downloading Core Datasets...")
subprocess.run([sys.executable, "-m", "gdown", "--folder", CORE_FOLDER_ID, "-O", dest_dir])

# Download Supporting datasets
print("Downloading Supporting Datasets...")
subprocess.run([sys.executable, "-m", "gdown", "--folder", SUPPORTING_FOLDER_ID, "-O", dest_dir])

print("Download process complete. Verifying downloaded files...")
files = os.listdir(dest_dir)
print(f"Total files in raw directory: {len(files)}")
print(files)
