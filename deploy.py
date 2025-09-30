import os
import hashlib
import json
import time
import requests
import secrets
from urllib.parse import quote

token = secrets.TOKEN
site_id = secrets.SITE_ID
site_folder = "site"

def compute_files_digest(folder: str) -> tuple:
    files = {}
    sha_to_paths = {}
    for root, _, filenames in os.walk(folder):
        for fname in filenames:
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, folder).replace(os.path.sep, "/")
            api_path = "/" + rel
            with open(full, "rb") as f:
                data = f.read()
            sha = hashlib.sha1(data).hexdigest()
            files[api_path] = sha
            sha_to_paths.setdefault(sha, []).append(rel)
    if not files:
        raise RuntimeError("No files found to deploy")
    return files, sha_to_paths

def create_digest_deploy(files_manifest: dict, token: str, site_id: str, async_mode: bool = False) -> dict:
    body = {"files": files_manifest}
    if async_mode:
        body["async"] = True
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = requests.post(f"https://api.netlify.com/api/v1/sites/{site_id}/deploys", headers=headers, data=json.dumps(body), timeout=60)
    resp.raise_for_status()
    return resp.json()

def upload_required_files(deploy_id: str, required_shas: list, sha_to_paths: dict, folder: str, token: str) -> None:
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream"}
    for sha in required_shas:
        paths = sha_to_paths.get(sha)
        if not paths:
            raise RuntimeError(f"No local file matches required sha {sha}")
        rel = paths[0]
        full = os.path.join(folder, rel)
        with open(full, "rb") as f:
            data = f.read()
        path_for_url = quote(rel, safe="/")
        url = f"https://api.netlify.com/api/v1/deploys/{deploy_id}/files/{path_for_url}"
        r = requests.put(url, headers=headers, data=data, timeout=120)
        r.raise_for_status()

def poll_deploy_ready(deploy_id: str, token: str, timeout: int = 300, interval: int = 3) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = requests.get(f"https://api.netlify.com/api/v1/deploys/{deploy_id}", headers=headers, timeout=30)
        r.raise_for_status()
        j = r.json()
        state = j.get("state")
        if state == "ready":
            return j
        if state in ("error", "failed"):
            return j
        time.sleep(interval)
    raise TimeoutError("Deploy did not reach ready state within timeout")

def main(dry_run: bool = False) -> None:
    files_manifest, sha_to_paths = compute_files_digest(site_folder)
    if dry_run:
        print("Dry run; files manifest:")
        for p, h in files_manifest.items():
            print(p, h)
        return
    deploy = create_digest_deploy(files_manifest, token, site_id, async_mode=False)
    deploy_id = deploy.get("id")
    required = deploy.get("required", [])
    if required:
        upload_required_files(deploy_id, required, sha_to_paths, site_folder, token)
    ready = poll_deploy_ready(deploy_id, token, timeout=300, interval=5)
    print("deploy state:", ready.get("state"))
    print("alias:", ready.get("links", {}).get("alias"))

if __name__ == "__main__":
    main(dry_run=False)

