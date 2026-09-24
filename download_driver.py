import json
import zipfile
import io
import os
import ssl
import urllib.request
import subprocess
import re

def get_chrome_version():
    """Detect local Chrome version on Windows"""
    import winreg
    
    # 1. Try registry keys
    reg_paths = [
        (winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon", "version"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Google Chrome", "DisplayVersion"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Google Chrome", "DisplayVersion"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Google Chrome", "DisplayVersion"),
    ]
    
    for hkey, path, val_name in reg_paths:
        try:
            key = winreg.OpenKey(hkey, path)
            version, _ = winreg.QueryValueEx(key, val_name)
            key.Close()
            if version:
                print(f"Detected Chrome version from registry ({path}\\{val_name}): {version}")
                return version.strip()
        except Exception:
            pass

    # 2. Try App Paths registry entries and check folder contents
    app_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
    ]
    for hkey, path in app_paths:
        try:
            key = winreg.OpenKey(hkey, path)
            exe_path, _ = winreg.QueryValueEx(key, "")
            key.Close()
            if exe_path and os.path.exists(exe_path):
                parent_dir = os.path.dirname(exe_path)
                if os.path.exists(parent_dir):
                    for item in os.listdir(parent_dir):
                        if re.match(r'^\d+\.\d+\.\d+\.\d+$', item):
                            print(f"Detected Chrome version from App Path directory structure: {item}")
                            return item
        except Exception:
            pass

    # 3. Try standard installation folders directly
    standard_paths = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application"),
    ]
    for folder in standard_paths:
        if os.path.exists(folder):
            for item in os.listdir(folder):
                if re.match(r'^\d+\.\d+\.\d+\.\d+$', item):
                    print(f"Detected Chrome version from standard path ({folder}): {item}")
                    return item

    # 4. Legacy PowerShell query as final fallback
    try:
        process = subprocess.Popen(
            ['powershell', '-command', '(Get-Item (Get-ItemProperty "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\chrome.exe")."(default)").VersionInfo.ProductVersion'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, text=True
        )
        stdout, _ = process.communicate()
        if stdout:
            version = stdout.strip()
            if version:
                print(f"Detected Chrome version from PowerShell fallback: {version}")
                return version
    except Exception as e:
        print(f"Error executing legacy PowerShell check: {e}")
    
    # Fallback to a default or return None
    return None

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
        
        chrome_version = get_chrome_version()
        major_version = "149" # Default based on browser version
        if chrome_version:
            major_version = chrome_version.split('.')[0]
        
        print(f"Targeting major version: {major_version}")
        
        target_version_data = None
        # Try to find exact major match first
        for v in reversed(versions):
            if v["version"].startswith(f"{major_version}."):
                downloads = v.get("downloads", {}).get("chromedriver", [])
                win64_dls = [d for d in downloads if d["platform"] == "win64"]
                if win64_dls:
                    target_version_data = v
                    break
        
        # If no match for current major, just take the absolute latest version
        if not target_version_data:
            print(f"Could not find a v{major_version} chromedriver! Taking the latest available...")
            for v in reversed(versions):
                downloads = v.get("downloads", {}).get("chromedriver", [])
                win64_dls = [d for d in downloads if d["platform"] == "win64"]
                if win64_dls:
                    target_version_data = v
                    break

        if not target_version_data:
            print("Could not find any chromedriver!")
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
