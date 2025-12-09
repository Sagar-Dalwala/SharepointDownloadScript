#!/usr/bin/env python3
"""
Simple Video Downloader - Test Script

Usage:
    python simple_download.py "YOUR_URL_HERE" "output_filename.mp4"
    
This script performs a simple ffmpeg download with minimal processing.
"""

import sys
import subprocess
from pathlib import Path

def trim_url(url: str) -> str:
    """Trim URL to format=dash"""
    marker = "&format=dash"
    if marker in url:
        return url[:url.find(marker) + len(marker)]
    return url

def simple_download(url: str, output_file: str):
    """Simple download using ffmpeg -i URL -c copy output.mp4"""
    
    print("=" * 60)
    print("Simple Video Downloader")
    print("=" * 60)
    
    # Trim URL
    trimmed_url = trim_url(url)
    print(f"\n📎 Original URL length: {len(url)}")
    print(f"📎 Trimmed URL length: {len(trimmed_url)}")
    
    output_path = Path(output_file)
    
    # Remove if exists
    if output_path.exists():
        print(f"\n🗑️  Removing existing file...")
        output_path.unlink()
    
    # Simple ffmpeg command
    cmd = [
        'ffmpeg',
        '-i', trimmed_url,
        '-c', 'copy',
        str(output_path)
    ]
    
    print(f"\n🎬 Downloading to: {output_path}")
    print(f"   Command: ffmpeg -i [URL] -c copy {output_file}")
    print(f"\n⏳ Please wait...\n")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=False,  # Show output in real-time
            text=True
        )
        
        if result.returncode == 0:
            if output_path.exists():
                size_mb = output_path.stat().st_size / (1024 * 1024)
                print(f"\n✅ SUCCESS! Downloaded: {size_mb:.1f} MB")
                print(f"   File: {output_path}")
                return True
            else:
                print(f"\n❌ FAILED: File was not created")
                return False
        else:
            print(f"\n❌ FAILED: ffmpeg returned error code {result.returncode}")
            return False
            
    except KeyboardInterrupt:
        print(f"\n⚠️  Interrupted by user")
        if output_path.exists():
            print(f"🗑️  Removing partial file...")
            output_path.unlink()
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

def main():
    if len(sys.argv) < 3:
        print("Usage: python simple_download.py \"URL\" \"output.mp4\"")
        print("\nExample:")
        print('python simple_download.py "https://centralindia1-mediap.svc.ms/..." "Lecture_01.mp4"')
        sys.exit(1)
    
    url = sys.argv[1]
    output = sys.argv[2]
    
    if not output.endswith('.mp4'):
        output = output + '.mp4'
    
    success = simple_download(url, output)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
