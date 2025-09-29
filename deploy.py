import os
import zipfile
import requests
import secrets

token = secrets.TOKEN
site_id = secrets.SITE_ID
folder_to_zip = "site"
zip_filename = "site.zip"

with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zf:
    for root, _, files in os.walk(folder_to_zip):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, folder_to_zip)
            zf.write(file_path, arcname)

with open(zip_filename, "rb") as f:
    deploy_zip = f.read()

headers = {"Authorization": f"Bearer {token}"}
files = {"zip": ("site.zip", deploy_zip, "application/zip")}

response = requests.post(f"https://api.netlify.com/api/v1/sites/{site_id}/builds", headers=headers, files=files)

print(response.status_code)
print(response.json())
