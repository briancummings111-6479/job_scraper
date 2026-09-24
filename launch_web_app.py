import os
import sys
import subprocess
import time
import re
import threading
import webbrowser

# Ensure UTF-8 output on Windows consoles
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except:
        pass

def find_python():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    venv_py = os.path.join(base_dir, ".venv", "Scripts", "python.exe")
    if os.path.exists(venv_py):
        return venv_py
    return sys.executable

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    python_exe = find_python()
    cloudflared_exe = os.path.join(base_dir, "bin", "cloudflared.exe")

    if not os.path.exists(cloudflared_exe):
        print(f"[ERROR] Cloudflare binary not found at {cloudflared_exe}", flush=True)
        return

    print("\n" + "="*65, flush=True)
    print("  🚀 CAREER MINER - SECURE CLOUDFLARE WEB TUNNEL LAUNCHER", flush=True)
    print("="*65 + "\n", flush=True)

    # 1. Start Flask App Subprocess
    print("[1/2] Launching Flask backend server on http://localhost:5000 ...", flush=True)
    app_env = os.environ.copy()
    app_env["PYTHONUNBUFFERED"] = "1"
    
    app_proc = subprocess.Popen(
        [python_exe, "app.py"],
        cwd=base_dir,
        env=app_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    time.sleep(2)

    # 2. Start Cloudflare Tunnel Subprocess
    print("[2/2] Connecting to Cloudflare global network...", flush=True)
    cf_proc = subprocess.Popen(
        [cloudflared_exe, "tunnel", "--url", "http://localhost:5000"],
        cwd=base_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )

    tunnel_url = None
    url_pattern = re.compile(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com')

    # Read output to capture the public URL
    start_time = time.time()
    while True:
        line = cf_proc.stdout.readline()
        if not line:
            if cf_proc.poll() is not None:
                break
            time.sleep(0.1)
            continue
        
        match = url_pattern.search(line)
        if match:
            tunnel_url = match.group(0)
            break
        if time.time() - start_time > 30:
            break

    if tunnel_url:
        print("\n" + "="*65, flush=True)
        print("  🎉 CAREER MINER IS NOW LIVE ON THE WEB!", flush=True)
        print("="*65, flush=True)
        print(f"\n  🌐 Shareable Web Link for Anyone:", flush=True)
        print(f"     👉 {tunnel_url}\n", flush=True)
        print(f"  💻 Local PC Link:", flush=True)
        print(f"     👉 http://localhost:5000\n", flush=True)
        print("  ✨ Anyone with this web link can access the dashboard,", flush=True)
        print("     run scrapes, and download or email Excel/PDF reports.", flush=True)
        print("="*65, flush=True)
        print("  Press Ctrl+C in this window anytime to stop the server.\n", flush=True)

        try:
            webbrowser.open(tunnel_url)
        except:
            pass

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[INFO] Stopping server and closing web tunnel...", flush=True)
    else:
        print("[WARN] Could not automatically extract public Cloudflare URL.", flush=True)

    try:
        cf_proc.terminate()
        app_proc.terminate()
    except:
        pass
    print("[OK] Stopped successfully.", flush=True)

if __name__ == '__main__':
    main()
