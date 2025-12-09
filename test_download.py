#!/usr/bin/env python3
"""
Test script - trying different ffmpeg options for DASH streams.
"""

import subprocess
import sys
import base64
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent / "test_downloads"


def extract_duration(url: str) -> float | None:
    """Extract expected duration from altManifestMetadata."""
    try:
        marker = 'altManifestMetadata='
        if marker not in url:
            return None
        start = url.find(marker) + len(marker)
        end = url.find('&', start)
        if end == -1:
            end = len(url)
        metadata_b64 = url[start:end]
        import urllib.parse
        metadata_b64 = urllib.parse.unquote(metadata_b64)
        padding = 4 - len(metadata_b64) % 4
        if padding != 4:
            metadata_b64 += '=' * padding
        metadata_json = base64.b64decode(metadata_b64).decode('utf-8')
        metadata = json.loads(metadata_json)
        duration_100nano = metadata.get('Duration100Nano', 0)
        return duration_100nano / 10_000_000
    except Exception as e:
        print(f"⚠️ Could not extract duration: {e}")
    return None


def trim_url(url: str) -> str:
    """Trim URL at format=dash."""
    marker = "&format=dash"
    if marker in url:
        return url[:url.find(marker) + len(marker)]
    return url


def format_duration(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def get_video_duration(filepath: Path) -> float | None:
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'csv=p=0', str(filepath)
        ], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except:
        pass
    return None


def download_with_options(url: str, output_path: Path, options: list, label: str, expected_duration: float = 600) -> bool:
    """Download video with specific ffmpeg options."""
    
    cmd = ['ffmpeg', '-y'] + options + ['-i', url, '-c', 'copy', str(output_path)]
    
    print(f"\n🎬 {label}")
    print(f"   Options: {' '.join(options) if options else '(none)'}")
    
    # Dynamic timeout: expected duration + 5 min buffer (minimum 10 min)
    timeout_secs = max(600, int(expected_duration) + 300)
    print(f"   Timeout: {timeout_secs // 60} minutes")
    print(f"   Downloading... (Ctrl+C to skip)")
    
    try:
        # Show progress by not capturing stderr
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_secs)
        
        if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 1000000:
            size_mb = output_path.stat().st_size / (1024 * 1024)
            dur = get_video_duration(output_path)
            print(f"   ✅ Success! Size: {size_mb:.1f} MB, Duration: {format_duration(dur) if dur else 'unknown'}")
            return True
        else:
            # Find error in stderr
            for line in result.stderr.split('\n'):
                if 'error' in line.lower() or 'Error' in line:
                    print(f"   ❌ {line.strip()[:100]}")
                    break
            else:
                print(f"   ❌ Failed (no specific error found)")
            return False
    except subprocess.TimeoutExpired:
        print(f"   ❌ Timeout")
        return False
    except Exception as e:
        print(f"   ❌ {e}")
        return False


def main():
    print("=" * 60)
    print("  🧪 Test Video Download - Multiple ffmpeg Options")
    print("=" * 60)
    
    url_file = SCRIPT_DIR / "test_url.txt"
    if not url_file.exists():
        print(f"\n❌ Please create: {url_file}")
        return
    
    original_url = url_file.read_text(encoding='utf-8').strip()
    if not original_url or 'videomanifest' not in original_url:
        print("❌ Invalid URL")
        return
    
    print(f"\n✅ Read URL ({len(original_url)} chars)")
    
    expected = extract_duration(original_url)
    if expected:
        print(f"📊 Expected duration: {format_duration(expected)}")
    
    print("\nEnter video name:")
    name = input().strip() or "test"
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    trimmed_url = trim_url(original_url)
    
    # Test different ffmpeg option combinations
    test_cases = [
        ([], "Default (no extra options)"),
        (['-protocol_whitelist', 'file,http,https,tcp,tls,crypto'], "Protocol whitelist"),
        (['-user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'], "With User-Agent"),
        (['-headers', 'Referer: https://cciitpatna-my.sharepoint.com/'], "With Referer header"),
        (['-reconnect', '1', '-reconnect_streamed', '1', '-reconnect_delay_max', '5'], "With reconnect options"),
    ]
    
    print("\n" + "=" * 60)
    print("Testing with TRIMMED URL (ends at format=dash)")
    print("=" * 60)
    
    exp_dur = expected if expected else 600  # Default 10 min if unknown
    
    for i, (options, label) in enumerate(test_cases):
        output = OUTPUT_DIR / f"{name}_test{i+1}.mp4"
        success = download_with_options(trimmed_url, output, options, label, exp_dur)
        if success:
            print(f"\n🎉 SUCCESS with: {label}")
            print(f"   Video saved to: {output}")
            if expected:
                actual = get_video_duration(output)
                if actual:
                    diff = abs(actual - expected)
                    print(f"   Duration diff: {diff:.1f} seconds")
            break
    else:
        print("\n❌ All approaches failed with trimmed URL")
        print("\nTrying FULL URL...")
        
        for i, (options, label) in enumerate(test_cases[:2]):  # Try first 2 with full URL
            output = OUTPUT_DIR / f"{name}_full{i+1}.mp4"
            success = download_with_options(original_url, output, options, label, exp_dur)
            if success:
                print(f"\n🎉 SUCCESS with full URL + {label}")
                break
    
    print("\n" + "=" * 60)
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
