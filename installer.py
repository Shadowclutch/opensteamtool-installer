import os
import winreg
import zipfile
import shutil
import requests

def get_steam_path():
    """Attempts to locate the Steam installation path via the Windows Registry."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
        steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
        winreg.CloseKey(key)
        return os.path.normpath(steam_path)
    except Exception:
        return r"C:\Program Files (x86)\Steam"

def main():
    # 1. Locate Steam Path
    steam_dir = get_steam_path()
    print(f"[*] Target Steam Path: {steam_dir}")
    
    if not os.path.exists(steam_dir):
        print(f"[!] Error: Steam directory not found at {steam_dir}")
        return

    # 2. Dynamically fetch the correct URL from GitHub API
    repo = "OpenSteam001/OpenSteamTool"
    api_url = f"https://api.github.com/repos/{repo}/releases/latest"
    print("[*] Fetching latest download link from GitHub API...")
    
    try:
        api_response = requests.get(api_url)
        api_response.raise_for_status()
        release_data = api_response.json()
        
        # Find the asset that matches the regular Release zip
        download_url = None
        for asset in release_data.get("assets", []):
            if "Release.zip" in asset.get("name", "") and "Debug" not in asset.get("name", ""):
                download_url = asset.get("browser_download_url")
                filename = asset.get("name")
                break
                
        if not download_url:
            print("[!] Could not find the Release ZIP file in the latest GitHub release assets.")
            return
            
        print(f"[+] Found asset: {filename}")
    except Exception as e:
        print(f"[!] Failed to communicate with GitHub API: {e}")
        return

    # 3. Define temporary paths
    temp_dir = os.environ.get("TEMP", os.getcwd())
    zip_path = os.path.join(temp_dir, filename)
    extract_path = os.path.join(temp_dir, "OpenSteamTool_Extracted")

    # 4. Download the file
    print(f"[*] Downloading {filename}...")
    try:
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        with open(zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("[+] Download complete.")
    except Exception as e:
        print(f"[!] Failed to download file: {e}")
        return

    # 5. Clean old extraction folder if it exists, then extract
    if os.path.exists(extract_path):
        shutil.rmtree(extract_path)
        
    print("[*] Extracting archive...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
    except Exception as e:
        print(f"[!] Extraction failed: {e}")
        return

    # 6. Move the required DLLs to the Steam Root Directory
    print("[*] Copying DLLs to Steam root...")
    required_dlls = ["dwmapi.dll", "xinput1_4.dll", "OpenSteamTool.dll"]
    
    for dll in required_dlls:
        source_file = os.path.join(extract_path, dll)
        destination_file = os.path.join(steam_dir, dll)
        
        if os.path.exists(source_file):
            try:
                shutil.copy2(source_file, destination_file)
                print(f"  -> Successfully copied {dll}")
            except PermissionError:
                print(f"[!] Permission Denied: Please run IDLE / Command Prompt as an Administrator.")
                return
            except Exception as e:
                print(f"[!] Failed to copy {dll}: {e}")
        else:
            print(f"[!] Warning: {dll} was not found in the downloaded archive.")

    # 7. Create the mandatory Lua config directory
    lua_config_path = os.path.join(steam_dir, "config", "lua")
    if not os.path.exists(lua_config_path):
        try:
            os.makedirs(lua_config_path)
            print(f"[+] Created required Lua config folder at: {lua_config_path}")
        except Exception as e:
            print(f"[!] Failed to create Lua config folder: {e}")
    else:
        print("[*] Lua config folder already exists.")

    # 8. Cleanup temporary setup files
    print("[*] Cleaning up temporary files...")
    if os.path.exists(zip_path):
        os.remove(zip_path)
    if os.path.exists(extract_path):
        shutil.rmtree(extract_path)

    print("[+] Automation complete! Make sure to fully restart Steam.")

if __name__ == "__main__":
    main()
