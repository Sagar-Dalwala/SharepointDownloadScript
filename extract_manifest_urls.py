#!/usr/bin/env python3
"""
SharePoint Video Manifest URL Extractor - Proxy Method

This script runs a proxy server that captures videomanifest URLs as you browse
SharePoint normally. Works for any subject/course!

Usage:
    python extract_manifest_urls.py

SETUP (one-time):
1. Run this script
2. Run enable_proxy.bat (as admin) to configure Windows proxy
3. Visit http://mitm.it to install the certificate (for HTTPS)
4. Browse to SharePoint and click on videos!
5. When done, run disable_proxy.bat
"""

import asyncio
import json
import os
import sys
import time
import threading
from pathlib import Path

# Configuration
SCRIPT_DIR = Path(__file__).parent
MANIFEST_FILE = SCRIPT_DIR / "manifest_urls.json"
PROXY_PORT = 8080

# Store captured URLs
captured_urls = []
seen_urls = set()
current_subject = "General"
lock = threading.Lock()


def trim_url(url: str) -> str:
    """Trim the videomanifest URL to end at &format=dash"""
    format_marker = "&format=dash"
    if format_marker in url:
        idx = url.find(format_marker)
        return url[:idx + len(format_marker)]
    return url


def save_results():
    """Save captured URLs to manifest_urls.json."""
    global captured_urls, current_subject
    
    if not captured_urls:
        print("\n❌ No URLs captured yet.")
        return
    
    # Load existing manifest
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
    else:
        manifest = {}
    
    # Ensure subject exists
    if current_subject not in manifest:
        manifest[current_subject] = []
    
    # Add new URLs (avoid duplicates)
    existing_urls = {v['url'] for v in manifest[current_subject]}
    
    for i, url in enumerate(captured_urls):
        if url not in existing_urls:
            lecture_num = len(manifest[current_subject]) + 1
            manifest[current_subject].append({
                'name': f"Lecture_{lecture_num:02d}",
                'url': url
            })
            existing_urls.add(url)
    
    # Save
    with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved {len(captured_urls)} URLs to {MANIFEST_FILE}")
    print(f"   Subject: {current_subject}")
    print(f"   Total lectures for this subject: {len(manifest[current_subject])}")


class ManifestCapture:
    """Mitmproxy addon to capture videomanifest URLs."""
    
    def request(self, flow):
        global captured_urls, seen_urls
        
        url = flow.request.url
        
        if 'videomanifest' in url:
            trimmed = trim_url(url)
            
            with lock:
                if trimmed not in seen_urls:
                    seen_urls.add(trimmed)
                    captured_urls.append(trimmed)
                    video_num = len(captured_urls)
                    print(f"\n  ✅ Captured manifest #{video_num}")
                    print(f"     URL: {trimmed[:80]}...")
                    print(f"\n> ", end='', flush=True)


async def run_proxy():
    """Run the mitmproxy asynchronously."""
    from mitmproxy import options
    from mitmproxy.tools.dump import DumpMaster
    
    opts = options.Options(listen_host='127.0.0.1', listen_port=PROXY_PORT)
    
    master = DumpMaster(
        opts,
        with_termlog=False,
        with_dumper=False,
    )
    
    master.addons.add(ManifestCapture())
    
    await master.run()


def start_proxy_thread():
    """Start proxy in a new thread with its own event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(run_proxy())
    except Exception as e:
        print(f"Proxy error: {e}")
    finally:
        loop.close()


def print_instructions():
    """Print setup instructions."""
    print("\n" + "=" * 60)
    print("  🌐 PROXY SETUP INSTRUCTIONS")
    print("=" * 60)
    print("""
  STEP 1: Enable the proxy
  -------------------------
  Run 'enable_proxy.bat' as Administrator
  (Right-click → Run as administrator)

  STEP 2: Install the certificate (one-time)
  -------------------------------------------
  1. Open Edge/Chrome
  2. Go to: http://mitm.it
  3. Click on "Windows" to download the certificate
  4. Double-click the downloaded file
  5. Click "Install Certificate..."
  6. Select "Current User" → Next
  7. Select "Place all certificates..." → Browse
  8. Choose "Trusted Root Certification Authorities" → OK → Next → Finish

  STEP 3: Browse to SharePoint
  -----------------------------
  1. Go to your SharePoint Recordings folder
  2. Click on each video one by one
  3. URLs will be captured automatically!

  STEP 4: When done
  ------------------
  Type 'quit' to save and exit
  Then run 'disable_proxy.bat' to restore normal browsing
""")
    print("=" * 60)


def interactive_mode():
    """Run interactive command loop."""
    global current_subject, captured_urls, seen_urls
    
    print_instructions()
    
    # First, set the subject
    print("\n📚 Available subjects in manifest:")
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
            for subj in manifest.keys():
                count = len(manifest[subj])
                print(f"   - {subj} ({count} lectures)")
    
    subject = input("\n📚 Enter subject name (or press Enter for 'AdvanceCyberSecurity'): ").strip()
    current_subject = subject if subject else "AdvanceCyberSecurity"
    
    print(f"\n✅ Subject set to: {current_subject}")
    print("\n🎬 Now browse to SharePoint and click on videos!")
    print("   Commands: 'view', 'save', 'subject', 'quit'")
    
    while True:
        try:
            cmd = input("\n> ").strip().lower()
            
            if cmd in ['q', 'quit', 'exit']:
                save_results()
                print("\n👋 Goodbye! Don't forget to run disable_proxy.bat!")
                os._exit(0)
                
            elif cmd in ['s', 'subject']:
                subject = input("Enter new subject name: ").strip()
                if subject:
                    if captured_urls:
                        save_choice = input("Save current URLs before switching? (y/n): ").strip().lower()
                        if save_choice == 'y':
                            save_results()
                    
                    current_subject = subject
                    captured_urls = []
                    seen_urls = set()
                    print(f"✅ Subject changed to: {current_subject}")
                    
            elif cmd in ['v', 'view']:
                if captured_urls:
                    print(f"\n📋 Captured URLs for '{current_subject}':")
                    for i, url in enumerate(captured_urls, 1):
                        print(f"  {i}. {url[:70]}...")
                else:
                    print("\n❌ No URLs captured yet. Click on some videos in SharePoint!")
                    
            elif cmd in ['c', 'clear']:
                if input("Are you sure? (y/n): ").strip().lower() == 'y':
                    captured_urls = []
                    seen_urls = set()
                    print("✅ Cleared all captured URLs.")
                    
            elif cmd in ['w', 'save', 'write']:
                save_results()
                
            elif cmd in ['h', 'help', 'menu', '?']:
                print("\n  Commands:")
                print("    [s] subject  - Change subject name")
                print("    [v] view     - View captured URLs")
                print("    [w] save     - Save URLs to file")
                print("    [c] clear    - Clear captured URLs")
                print("    [q] quit     - Save and exit")
                
            elif cmd == '':
                print(f"  [{current_subject}] {len(captured_urls)} URLs captured")
                
            else:
                print("  Unknown command. Type 'help' for options.")
                
        except EOFError:
            save_results()
            break
        except KeyboardInterrupt:
            save_results()
            print("\n\n👋 Goodbye! Don't forget to run disable_proxy.bat!")
            os._exit(0)


def main():
    print("=" * 60)
    print("  📹 SharePoint Video Manifest URL Extractor")
    print("  (Proxy Method - Works for all courses!)")
    print("=" * 60)
    print("\n🚀 Starting proxy server on 127.0.0.1:8080...")
    
    # Start proxy in background thread
    proxy_thread = threading.Thread(target=start_proxy_thread, daemon=True)
    proxy_thread.start()
    
    time.sleep(2)  # Wait for proxy to start
    
    print("✅ Proxy server is running!")
    
    # Run interactive mode
    interactive_mode()


if __name__ == "__main__":
    main()
