import os
import zipfile
import requests
import secrets

def get_site_name(token, site_id):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"https://api.netlify.com/api/v1/sites/{site_id}", headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get("name", site_id)
    return site_id

def zip_folder(folder_to_zip, zip_filename):
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(folder_to_zip):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_to_zip)
                zf.write(file_path, arcname)

def deploy_site(token, site_id, zip_filename):
    with open(zip_filename, "rb") as f:
        deploy_zip = f.read()
    headers = {"Authorization": f"Bearer {token}"}
    files = {"zip": (zip_filename, deploy_zip, "application/zip")}
    response = requests.post(f"https://api.netlify.com/api/v1/sites/{site_id}/builds", headers=headers, files=files)
    print(response.status_code)
    print(response.json())

def main():
    token = secrets.TOKEN
    default_site_id = secrets.SITE_ID
    default_name = get_site_name(token, default_site_id)
    user_input = input(f"Project ID (default '{default_name}'): ").strip()
    site_id = user_input if user_input else default_site_id
    folder_to_zip = "site"
    zip_filename = "site.zip"
    zip_folder(folder_to_zip, zip_filename)
    deploy_site(token, site_id, zip_filename)

if __name__ == "__main__":
    main()

