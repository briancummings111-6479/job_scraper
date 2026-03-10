import json
import zipfile
import io
import os
import ssl
import urllib.request

def download_chromedriver():
    url = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
    print("Fetching all known good versions...")
    
    # Bypass SSL verification to avoid WinError 10054 related to TLS interception
    context = ssl._create_unverified_context()
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=context) as response:
            data = json.loads(response.read().decode())
            
        versions = data.get("versions", [])
        
        # We want the newest version that starts with 145
        target_version_data = None
        for v in reversed(versions):
            if v["version"].startswith("145."):
                # Check if it has chromedriver for win64
                downloads = v.get("downloads", {}).get("chromedriver", [])
                win64_dls = [d for d in downloads if d["platform"] == "win64"]
                if win64_dls:
                    target_version_data = v
                    break
        
        if not target_version_data:
            print("Could not find a v145 chromedriver!")
            return
            
        version = target_version_data["version"]
        print(f"Selecting version: {version}")
        
        downloads = target_version_data["downloads"]["chromedriver"]
        win64_url = next(d["url"] for d in downloads if d["platform"] == "win64")
        print(f"Download URL: {win64_url}")
        
        print("Downloading zip...")
        zip_req = urllib.request.Request(win64_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(zip_req, context=context) as zip_resp:
            content = zip_resp.read()
            
        print("Extracting...")
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            for file_info in z.infolist():
                if file_info.filename.endswith('chromedriver.exe'):
                    # Extract to drivers/chromedriver.exe
                    file_info.filename = 'chromedriver.exe'
                    target_dir = os.path.join(os.getcwd(), 'drivers')
                    os.makedirs(target_dir, exist_ok=True)
                    z.extract(file_info, target_dir)
                    print(f"Successfully extracted to {target_dir}\\chromedriver.exe")
                    return
                    
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    download_chromedriver()
