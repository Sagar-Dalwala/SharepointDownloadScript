#!/usr/bin/env python3
"""
SharePoint/Teams Lecture Video Downloader

This script automates downloading lecture recordings from SharePoint/Teams
using videomanifest URLs with either ffmpeg or yt-dlp.

DOWNLOADER OPTIONS:
    - yt-dlp:  FAST - downloads video segments in parallel (recommended)
    - ffmpeg:  Reliable - downloads segments sequentially

Usage:
    python download_lectures.py                     # Interactive downloader selection
    python download_lectures.py -d ytdlp            # Use yt-dlp (fast)
    python download_lectures.py -d ytdlp -f 8       # yt-dlp with 8 parallel fragments
    python download_lectures.py -d ffmpeg           # Use ffmpeg (reliable)
    python download_lectures.py --parallel 3        # Download 3 videos at once
    python download_lectures.py --retry             # Retry only failed downloads
    python download_lectures.py --retry -d ytdlp    # Retry with yt-dlp
    
The script reads URLs from manifest_urls.json in the same directory.
"""


import json
import os
import subprocess
import sys
import argparse
import threading
import base64
import time
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
SCRIPT_DIR = Path(__file__).parent
MANIFEST_FILE = SCRIPT_DIR / "manifest_urls.json"
FAILED_LOG = SCRIPT_DIR / "failed_downloads.json"
BASE_DIR = SCRIPT_DIR.parent  # d:\IITP

# Validation settings
DURATION_TOLERANCE = 10  # seconds - allow 10 second difference (relaxed for 429 errors)
MIN_FILE_SIZE = 1_000_000  # 1 MB minimum

# Rate limiting to avoid 429 errors
DELAY_BETWEEN_DOWNLOADS = 3  # seconds between each download
MAX_RETRIES_ON_429 = 2  # retry attempts for 429 errors
RETRY_DELAY_429 = 30  # seconds to wait after 429 error

# Notification settings
ENABLE_NOTIFICATIONS = True

# Downloader settings
DEFAULT_CONCURRENT_FRAGMENTS = 4  # yt-dlp concurrent fragment downloads

# Global list to track failed downloads (thread-safe with lock)
failed_downloads = []
failed_downloads_lock = threading.Lock()

# Global downloader settings (set at runtime)
selected_downloader = "ffmpeg"  # "ffmpeg" or "ytdlp"
concurrent_fragments = DEFAULT_CONCURRENT_FRAGMENTS

# Try to import notification library
try:
    from plyer import notification
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False


def send_notification(title: str, message: str, timeout: int = 10):
    """Send desktop notification."""
    if not ENABLE_NOTIFICATIONS:
        return
    
    if not NOTIFICATIONS_AVAILABLE:
        return
    
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="Lecture Downloader",
            timeout=timeout
        )
    except Exception as e:
        # Silently fail if notifications don't work
        pass


def extract_duration_from_url(url: str) -> float:
    """
    Extract expected duration from altManifestMetadata in the URL.
    Returns duration in seconds, or None if not found.
    """
    try:
        marker = 'altManifestMetadata='
        if marker not in url:
            return None
        
        start = url.find(marker) + len(marker)
        end = url.find('&', start)
        if end == -1:
            end = len(url)
        
        metadata_b64 = url[start:end]
        
        # URL decode
        import urllib.parse
        metadata_b64 = urllib.parse.unquote(metadata_b64)
        
        # Add padding if needed
        padding = 4 - len(metadata_b64) % 4
        if padding != 4:
            metadata_b64 += '=' * padding
        
        # Decode base64
        metadata_json = base64.b64decode(metadata_b64).decode('utf-8')
        metadata = json.loads(metadata_json)
        
        # Duration is in 100-nanosecond units
        duration_100nano = metadata.get('Duration100Nano', 0)
        duration_seconds = duration_100nano / 10_000_000
        
        return duration_seconds
    except Exception as e:
        return None


def format_duration(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def get_video_duration(filepath: Path) -> float:
    """Get actual duration of downloaded video using ffprobe."""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'csv=p=0',
            str(filepath)
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except Exception as e:
        print(f"   ⚠️ Could not verify duration: {e}")
    return None


def validate_video(filepath: Path, expected_duration: float = None) -> tuple:
    """
    Validate downloaded video file.
    
    Returns:
        (is_valid: bool, message: str)
    """
    # Check file exists
    if not filepath.exists():
        return False, "File does not exist"
    
    # Check minimum file size
    file_size = filepath.stat().st_size
    if file_size < MIN_FILE_SIZE:
        return False, f"File too small ({file_size} bytes)"
    
    # Check duration if expected duration provided
    if expected_duration:
        actual_duration = get_video_duration(filepath)
        if actual_duration is None:
            return False, "Could not read video duration"
        
        duration_diff = abs(actual_duration - expected_duration)
        
        if duration_diff > DURATION_TOLERANCE:
            return False, (f"Duration mismatch: expected {format_duration(expected_duration)}, "
                          f"got {format_duration(actual_duration)} "
                          f"(diff: {duration_diff:.1f}s)")
        
        return True, f"Valid: {format_duration(actual_duration)}"
    
    return True, f"Valid: {file_size / (1024*1024):.1f} MB"


def check_ytdlp_available() -> bool:
    """Check if yt-dlp is available on the system."""
    try:
        result = subprocess.run(['yt-dlp', '--version'], 
                               capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_ffmpeg_available() -> bool:
    """Check if ffmpeg is available on the system."""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                               capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def select_downloader() -> tuple:
    """
    Interactive prompt to let user select downloader.
    Returns (downloader_name, concurrent_fragments)
    """
    global selected_downloader, concurrent_fragments
    
    ffmpeg_available = check_ffmpeg_available()
    ytdlp_available = check_ytdlp_available()
    
    print("\n📥 Select Download Method:")
    print("=" * 40)
    
    options = []
    
    if ytdlp_available:
        options.append(("ytdlp", "yt-dlp (Fast - parallel segment downloads)"))
        print(f"  1. yt-dlp  ⚡ FAST - Downloads segments in parallel")
    else:
        print(f"  1. yt-dlp  ❌ NOT INSTALLED (pip install yt-dlp)")
    
    if ffmpeg_available:
        options.append(("ffmpeg", "ffmpeg (Reliable - sequential downloads)"))
        print(f"  2. ffmpeg  ✅ Reliable - Downloads segments sequentially")
    else:
        print(f"  2. ffmpeg  ❌ NOT INSTALLED")
    
    print("=" * 40)
    
    if not ffmpeg_available and not ytdlp_available:
        print("❌ No downloader available! Please install ffmpeg or yt-dlp.")
        return None, None
    
    # Default choice
    default_choice = "1" if ytdlp_available else "2"
    
    while True:
        choice = input(f"\nEnter your choice (1 or 2) [default: {default_choice}]: ").strip()
        if choice == "":
            choice = default_choice
        
        if choice == "1":
            if ytdlp_available:
                selected_downloader = "ytdlp"
                # Ask for concurrent fragments
                frag_input = input(f"Number of parallel downloads (1-16) [default: {DEFAULT_CONCURRENT_FRAGMENTS}]: ").strip()
                if frag_input == "":
                    concurrent_fragments = DEFAULT_CONCURRENT_FRAGMENTS
                else:
                    try:
                        concurrent_fragments = max(1, min(16, int(frag_input)))
                    except ValueError:
                        concurrent_fragments = DEFAULT_CONCURRENT_FRAGMENTS
                print(f"\n✅ Using yt-dlp with {concurrent_fragments} parallel segment downloads")
                return "ytdlp", concurrent_fragments
            else:
                print("❌ yt-dlp is not installed. Please install with: pip install yt-dlp")
        elif choice == "2":
            if ffmpeg_available:
                selected_downloader = "ffmpeg"
                print("\n✅ Using ffmpeg for downloads")
                return "ffmpeg", 1
            else:
                print("❌ ffmpeg is not installed. Please install ffmpeg.")
        else:
            print("Invalid choice. Please enter 1 or 2.")


def download_video_ytdlp(url: str, output_path: Path, subject: str = "", 
                          name: str = "", original_url: str = "",
                          num_fragments: int = 4, retry_count: int = 0) -> bool:
    """
    Download video using yt-dlp (faster due to parallel segment downloads).
    
    Args:
        url: The trimmed videomanifest URL
        output_path: Full path for the output MP4 file
        subject: Subject name (for logging)
        name: Video name (for logging)
        original_url: Original full URL (for duration extraction and logging)
        num_fragments: Number of fragments to download in parallel
        retry_count: Current retry attempt for errors
    
    Returns:
        True if successful, False otherwise
    """
    if output_path.exists():
        # Check if file is valid before skipping
        file_size = output_path.stat().st_size
        if file_size > MIN_FILE_SIZE:
            print(f"⏭️  Skipping (already exists): {output_path.name} ({file_size / (1024*1024):.1f} MB)")
            return True
        else:
            print(f"🗑️  Removing invalid existing file: {output_path.name}")
            output_path.unlink()
    
    # Extract expected duration
    expected_duration = extract_duration_from_url(original_url or url)
    
    # yt-dlp command with parallel downloads
    cmd = [
        'yt-dlp',
        '--no-part',                    # Don't use .part files
        '-N', str(num_fragments),       # Concurrent fragment downloads
        '-o', str(output_path),         # Output path
        '--no-warnings',                # Suppress warnings
        '--progress',                   # Show progress
        url
    ]
    
    print(f"\n🎬 Downloading: {output_path.name}")
    print(f"   To: {output_path.parent}")
    print(f"   Method: yt-dlp with {num_fragments} parallel downloads")
    if expected_duration:
        print(f"   Expected duration: {format_duration(expected_duration)}")
    
    try:
        # Run yt-dlp with timeout
        timeout_seconds = max(1800, int(expected_duration) + 600) if expected_duration else 1800
        
        start_time = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        elapsed_time = time.time() - start_time
        
        if result.returncode == 0:
            # Check if file was created and has reasonable size
            if not output_path.exists():
                print(f"   ❌ File was not created")
                return False
            
            file_size = output_path.stat().st_size
            
            if file_size < MIN_FILE_SIZE:
                print(f"   ❌ File too small ({file_size} bytes) - likely failed")
                output_path.unlink()
                return False
            
            # Quick validation
            if expected_duration:
                actual_duration = get_video_duration(output_path)
                if actual_duration:
                    duration_diff = abs(actual_duration - expected_duration)
                    
                    if duration_diff > DURATION_TOLERANCE:
                        print(f"   ⚠️  Duration mismatch: expected {format_duration(expected_duration)}, got {format_duration(actual_duration)} (diff: {duration_diff:.1f}s)")
                        print(f"   ℹ️  Keeping file anyway (within relaxed tolerance)")
                    else:
                        print(f"   ✅ Duration valid: {format_duration(actual_duration)}")
            
            file_size_mb = file_size / (1024 * 1024)
            print(f"   ✅ Downloaded successfully ({file_size_mb:.1f} MB in {elapsed_time:.0f}s)")
            return True
            
        else:
            # Check for specific errors
            stderr_lower = result.stderr.lower() if result.stderr else ""
            stdout_lower = result.stdout.lower() if result.stdout else ""
            combined_output = stderr_lower + stdout_lower
            
            # 429 Too Many Requests - rate limiting
            if '429' in combined_output or 'too many requests' in combined_output:
                if retry_count < MAX_RETRIES_ON_429:
                    print(f"   ⚠️  Rate limited (429 Too Many Requests)")
                    print(f"   ⏳ Waiting {RETRY_DELAY_429} seconds before retry {retry_count + 1}/{MAX_RETRIES_ON_429}...")
                    time.sleep(RETRY_DELAY_429)
                    return download_video_ytdlp(url, output_path, subject, name, original_url, num_fragments, retry_count + 1)
                else:
                    error_msg = "Rate limited (429) - too many requests. Try again later."
                    print(f"   ❌ {error_msg}")
                    with failed_downloads_lock:
                        failed_downloads.append({
                            "subject": subject,
                            "name": name,
                            "url": "",
                            "error": error_msg
                        })
                    return False
            
            # 403/401 - likely expired URL
            if '403' in combined_output or '401' in combined_output or 'forbidden' in combined_output or 'unauthorized' in combined_output:
                error_msg = "Authentication error (403/401) - URL may have expired"
                print(f"   ❌ {error_msg}")
                with failed_downloads_lock:
                    failed_downloads.append({
                        "subject": subject,
                        "name": name,
                        "url": "",
                        "error": error_msg
                    })
                return False
            
            # Generic error
            error_msg = result.stderr[:500] if result.stderr else "Unknown error"
            print(f"   ❌ Failed to download: {output_path.name}")
            print(f"   Error: {error_msg}")
            
            with failed_downloads_lock:
                failed_downloads.append({
                    "subject": subject,
                    "name": name,
                    "url": "",
                    "error": error_msg
                })
            return False
                
    except subprocess.TimeoutExpired:
        error_msg = f"Download timeout after {timeout_seconds // 60} minutes"
        print(f"   ❌ {error_msg}")
        if output_path.exists():
            output_path.unlink()
        
        with failed_downloads_lock:
            failed_downloads.append({
                "subject": subject,
                "name": name,
                "url": "",
                "error": error_msg
            })
        return False
    except FileNotFoundError:
        print("❌ yt-dlp not found! Please install: pip install yt-dlp")
        return False
    except Exception as e:
        error_msg = str(e)
        print(f"   ❌ Error downloading {output_path.name}: {error_msg}")
        if output_path.exists():
            output_path.unlink()
        
        with failed_downloads_lock:
            failed_downloads.append({
                "subject": subject,
                "name": name,
                "url": "",
                "error": error_msg
            })
        return False


def load_manifest():
    """Load the manifest URLs from JSON file."""
    if not MANIFEST_FILE.exists():
        print(f"❌ Manifest file not found: {MANIFEST_FILE}")
        print("Creating a sample manifest file for you to fill in...")
        create_sample_manifest()
        return None
    
    with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)



def create_sample_manifest():
    """Create a sample manifest file."""
    sample = {
        "AML": [
            {
                "name": "Lecture_01_Introduction",
                "url": "PASTE_YOUR_VIDEOMANIFEST_URL_HERE"
            }
        ],
        "DAA": [],
        "AdvanceCyberSecurity": [],
        "Prob&Stat": [],
        "TechWrite&SoftSkills": []
    }
    
    with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(sample, f, indent=2)
    
    print(f"✅ Sample manifest created at: {MANIFEST_FILE}")
    print("Please edit this file and add your videomanifest URLs.")


def trim_url(url: str) -> str:
    """
    Trim the videomanifest URL to end at &format=dash
    
    This follows the pattern:
    - Keep everything from https://.../videomanifest up to &format=dash
    - Delete anything after format=dash
    """
    # Find the position of &format=dash or format=dash
    format_marker = "&format=dash"
    alt_marker = "format=dash"
    
    if format_marker in url:
        idx = url.find(format_marker)
        return url[:idx + len(format_marker)]
    elif alt_marker in url:
        idx = url.find(alt_marker)
        return url[:idx + len(alt_marker)]
    else:
        # If format=dash not found, return as-is (might be a different URL type)
        print("⚠️ Warning: 'format=dash' not found in URL, using as-is")
        return url


def get_available_subjects(manifest: dict) -> list:
    """Get list of subjects that have videos to download."""
    return [subject for subject, videos in manifest.items() if videos]


def list_existing_folders() -> list:
    """List existing subject folders in BASE_DIR."""
    folders = []
    for item in BASE_DIR.iterdir():
        if item.is_dir() and not item.name.startswith('.') and item.name != 'scripts':
            folders.append(item.name)
    return sorted(folders)


def select_subject(manifest: dict) -> str:
    """Let user select which subject to download."""
    print("\n📚 Available subjects with videos:")
    subjects = get_available_subjects(manifest)
    
    if not subjects:
        print("❌ No subjects with videos found in manifest.")
        print("Please add URLs to manifest_urls.json")
        return None
    
    for i, subject in enumerate(subjects, 1):
        video_count = len(manifest[subject])
        print(f"  {i}. {subject} ({video_count} videos)")
    
    print(f"\n  0. Download ALL subjects")
    
    while True:
        try:
            choice = input("\nEnter your choice (number): ").strip()
            if choice == '0':
                return "ALL"
            
            idx = int(choice) - 1
            if 0 <= idx < len(subjects):
                return subjects[idx]
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a valid number.")


def ensure_lectures_folder(subject: str) -> Path:
    """Create subject folder and Lectures subfolder if they don't exist."""
    subject_dir = BASE_DIR / subject
    lectures_dir = subject_dir / "Lectures"
    
    if not subject_dir.exists():
        print(f"📁 Creating subject folder: {subject_dir}")
        subject_dir.mkdir(parents=True, exist_ok=True)
    
    if not lectures_dir.exists():
        print(f"📁 Creating Lectures folder: {lectures_dir}")
        lectures_dir.mkdir(parents=True, exist_ok=True)
    
    return lectures_dir


def ensure_all_folders_from_manifest(manifest: dict):
    """Create all subject folders mentioned in the manifest."""
    print("\n📁 Ensuring all subject folders exist...")
    for subject in manifest.keys():
        subject_dir = BASE_DIR / subject
        if not subject_dir.exists():
            print(f"   Creating: {subject}")
            subject_dir.mkdir(parents=True, exist_ok=True)
        
        lectures_dir = subject_dir / "Lectures"
        if not lectures_dir.exists():
            lectures_dir.mkdir(parents=True, exist_ok=True)
    print("✅ All folders ready")



def extract_ffmpeg_error(stderr: str) -> str:
    """Extract the actual error message from ffmpeg stderr."""
    if not stderr:
        return "Unknown error (no stderr output)"
    
    error_lines = []
    for line in stderr.split('\n'):
        line_lower = line.lower()
        # Look for common error indicators
        if any(indicator in line_lower for indicator in [
            'error', 'failed', 'invalid', 'denied', 'forbidden', 
            'unauthorized', 'timeout', 'refused', 'not found', '403', '401', '404'
        ]):
            error_lines.append(line.strip())
    
    if error_lines:
        # Return the most relevant error lines (up to 5)
        return '\n   '.join(error_lines[:5])
    else:
        # If no obvious error found, return last few non-empty lines
        lines = [l.strip() for l in stderr.split('\n') if l.strip()]
        return '\n   '.join(lines[-3:]) if lines else "Unknown error"


def save_failed_downloads():
    """Save failed downloads to a JSON file for later retry."""
    if failed_downloads:
        with open(FAILED_LOG, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "failed": failed_downloads
            }, f, indent=2)
        print(f"\n📝 Failed downloads saved to: {FAILED_LOG}")


def load_failed_downloads() -> list:
    """Load previously failed downloads from JSON file."""
    if not FAILED_LOG.exists():
        return []
    
    with open(FAILED_LOG, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('failed', [])


def download_video(url: str, output_path: Path, subject: str = "", name: str = "", original_url: str = "", use_reencode: bool = False, retry_count: int = 0) -> bool:
    """
    Download video using ffmpeg with simple approach.
    
    Args:
        url: The trimmed videomanifest URL
        output_path: Full path for the output MP4 file
        subject: Subject name (for logging)
        name: Video name (for logging)
        original_url: Original full URL (for duration extraction and logging)
        use_reencode: If True, re-encode instead of codec copy
        retry_count: Current retry attempt for 429 errors
    
    Returns:
        True if successful, False otherwise
    """
    if output_path.exists():
        # Check if file is valid before skipping
        file_size = output_path.stat().st_size
        if file_size > MIN_FILE_SIZE:
            print(f"⏭️  Skipping (already exists): {output_path.name} ({file_size / (1024*1024):.1f} MB)")
            return True
        else:
            print(f"🗑️  Removing invalid existing file: {output_path.name}")
            output_path.unlink()
    
    # Extract expected duration
    expected_duration = extract_duration_from_url(original_url or url)
    
    # Simple ffmpeg command - just copy codecs (fastest)
    if use_reencode:
        cmd = [
            'ffmpeg', '-y',
            '-i', url,
            '-c:v', 'libx264', '-preset', 'fast',
            '-c:a', 'aac', '-b:a', '128k',
            str(output_path)
        ]
        method = "re-encoding"
    else:
        # Simple codec copy - no transcoding
        cmd = [
            'ffmpeg', '-y',
            '-i', url,
            '-c', 'copy',
            str(output_path)
        ]
        method = "codec copy"
    
    print(f"\n🎬 Downloading: {output_path.name}")
    print(f"   To: {output_path.parent}")
    print(f"   Method: {method}")
    if expected_duration:
        print(f"   Expected duration: {format_duration(expected_duration)}")
    
    try:
        # Run ffmpeg with timeout
        timeout_seconds = max(1800, int(expected_duration) + 600) if expected_duration else 1800
        
        start_time = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        elapsed_time = time.time() - start_time
        
        if result.returncode == 0:
            # Check if file was created and has reasonable size
            if not output_path.exists():
                print(f"   ❌ File was not created")
                return False
            
            file_size = output_path.stat().st_size
            
            if file_size < MIN_FILE_SIZE:
                print(f"   ❌ File too small ({file_size} bytes) - likely failed")
                output_path.unlink()
                return False
            
            # Quick validation - relaxed tolerance
            if expected_duration:
                actual_duration = get_video_duration(output_path)
                if actual_duration:
                    duration_diff = abs(actual_duration - expected_duration)
                    
                    if duration_diff > DURATION_TOLERANCE:
                        print(f"   ⚠️  Duration mismatch: expected {format_duration(expected_duration)}, got {format_duration(actual_duration)} (diff: {duration_diff:.1f}s)")
                        print(f"   ℹ️  Keeping file anyway (within relaxed tolerance)")
                    else:
                        print(f"   ✅ Duration valid: {format_duration(actual_duration)}")
            
            file_size_mb = file_size / (1024 * 1024)
            print(f"   ✅ Downloaded successfully ({file_size_mb:.1f} MB in {elapsed_time:.0f}s)")
            return True
            
        else:
            # Check for specific errors
            stderr_lower = result.stderr.lower()
            
            # 429 Too Many Requests - rate limiting
            if '429' in result.stderr or 'too many requests' in stderr_lower:
                if retry_count < MAX_RETRIES_ON_429:
                    print(f"   ⚠️  Rate limited (429 Too Many Requests)")
                    print(f"   ⏳ Waiting {RETRY_DELAY_429} seconds before retry {retry_count + 1}/{MAX_RETRIES_ON_429}...")
                    time.sleep(RETRY_DELAY_429)
                    return download_video(url, output_path, subject, name, original_url, use_reencode, retry_count + 1)
                else:
                    error_msg = "Rate limited (429) - too many requests. Try again later or reduce parallel downloads."
                    print(f"   ❌ {error_msg}")
                    with failed_downloads_lock:
                        failed_downloads.append({
                            "subject": subject,
                            "name": name,
                            "url": "",
                            "error": error_msg
                        })
                    return False
            
            # 403/401 - likely expired URL
            if '403' in result.stderr or '401' in result.stderr or 'forbidden' in stderr_lower or 'unauthorized' in stderr_lower:
                error_msg = "Authentication error (403/401) - URL may have expired"
                print(f"   ❌ {error_msg}")
                with failed_downloads_lock:
                    failed_downloads.append({
                        "subject": subject,
                        "name": name,
                        "url": "",
                        "error": error_msg
                    })
                return False
            
            # If codec copy failed and we haven't tried re-encoding yet
            if not use_reencode:
                print(f"   ⚠️  Codec copy failed, trying re-encode...")
                # Small delay before retry
                time.sleep(2)
                return download_video(url, output_path, subject, name, original_url, use_reencode=True, retry_count=0)
            else:
                error_msg = extract_ffmpeg_error(result.stderr)
                print(f"   ❌ Failed to download: {output_path.name}")
                print(f"   Error: {error_msg}")
                
                with failed_downloads_lock:
                    failed_downloads.append({
                        "subject": subject,
                        "name": name,
                        "url": "",
                        "error": error_msg
                    })
                return False
                
    except subprocess.TimeoutExpired:
        error_msg = f"Download timeout after {timeout_seconds // 60} minutes"
        print(f"   ❌ {error_msg}")
        if output_path.exists():
            output_path.unlink()
        
        with failed_downloads_lock:
            failed_downloads.append({
                "subject": subject,
                "name": name,
                "url": "",
                "error": error_msg
            })
        return False
    except FileNotFoundError:
        print("❌ ffmpeg not found! Please install ffmpeg and add it to PATH.")
        print("   Download from: https://ffmpeg.org/download.html")
        return False
    except Exception as e:
        error_msg = str(e)
        print(f"   ❌ Error downloading {output_path.name}: {error_msg}")
        if output_path.exists():
            output_path.unlink()
        
        with failed_downloads_lock:
            failed_downloads.append({
                "subject": subject,
                "name": name,
                "url": "",
                "error": error_msg
            })
        return False



def download_single_video(args):
    """
    Download a single video. Used as a worker function for parallel downloads.
    Includes rate limiting delay to avoid 429 errors.
    
    Args:
        args: tuple of (subject, video, lectures_dir, retry_only)
    
    Returns:
        tuple of (success: bool, video_name: str)
    """
    global selected_downloader, concurrent_fragments
    
    subject, video, lectures_dir, retry_only = args
    
    name = video.get('name', 'Unknown')
    url = video.get('url', '')
    
    if not url or url == "PASTE_YOUR_VIDEOMANIFEST_URL_HERE":
        print(f"⏭️  Skipping {name}: No valid URL")
        return (None, name)  # None = skipped
    
    # Store original URL for duration extraction
    original_url = url
    original_name = name
    
    # Ensure name ends with .mp4
    if not name.endswith('.mp4'):
        name = f"{name}.mp4"
    
    output_path = lectures_dir / name
    
    # For retry mode, delete partial/failed files first
    if retry_only and output_path.exists():
        print(f"🗑️  Removing failed file for retry: {name}")
        output_path.unlink()
    
    # Trim the URL
    trimmed_url = trim_url(url)
    
    # Download using selected downloader
    if selected_downloader == "ytdlp":
        success = download_video_ytdlp(trimmed_url, output_path, subject, original_name, original_url, concurrent_fragments)
    else:
        success = download_video(trimmed_url, output_path, subject, original_name, original_url)
    
    # Rate limiting delay between downloads to avoid 429 errors
    if DELAY_BETWEEN_DOWNLOADS > 0:
        time.sleep(DELAY_BETWEEN_DOWNLOADS)
    
    return (success, original_name)



def download_subject(subject: str, videos: list, retry_only: list = None, parallel_workers: int = 1) -> tuple:
    """Download all videos for a subject.
    
    Args:
        subject: Subject name
        videos: List of video dicts with 'name' and 'url'
        retry_only: If provided, only download videos whose names are in this list
        parallel_workers: Number of parallel downloads (1 = sequential)
                         Note: Use 1-2 max to avoid 429 rate limiting errors
    """
    lectures_dir = ensure_lectures_folder(subject)
    
    success_count = 0
    fail_count = 0
    
    # Filter videos if retry_only is set
    if retry_only:
        videos_to_download = [v for v in videos if v.get('name') in retry_only]
        if not videos_to_download:
            return 0, 0
    else:
        videos_to_download = videos
    
    print(f"\n{'='*50}")
    print(f"📖 Subject: {subject}")
    print(f"   Videos to download: {len(videos_to_download)}")
    print(f"   Destination: {lectures_dir}")
    if parallel_workers > 1:
        print(f"   🚀 Parallel downloads: {parallel_workers}")
        print(f"   ⏳ Rate limiting: {DELAY_BETWEEN_DOWNLOADS}s delay between downloads")
    print(f"{'='*50}")
    
    # Prepare arguments for each video
    download_args = [(subject, video, lectures_dir, retry_only) for video in videos_to_download]
    
    if parallel_workers > 1:
        # Parallel download mode - use with caution for 429 errors
        print(f"\n⚠️  Warning: Parallel downloads may cause rate limiting (429 errors)")
        print(f"   Recommended: Use --parallel 1 or 2 maximum\n")
        
        with ThreadPoolExecutor(max_workers=parallel_workers) as executor:
            futures = {executor.submit(download_single_video, args): args[1].get('name', 'Unknown') 
                      for args in download_args}
            
            for future in as_completed(futures):
                video_name = futures[future]
                try:
                    success, name = future.result()
                    if success is None:
                        # Skipped
                        pass
                    elif success:
                        success_count += 1
                    else:
                        fail_count += 1
                except Exception as e:
                    print(f"❌ Exception downloading {video_name}: {e}")
                    fail_count += 1
    else:
        # Sequential download mode (RECOMMENDED to avoid 429 errors)
        for args in download_args:
            success, name = download_single_video(args)
            if success is None:
                pass  # Skipped
            elif success:
                success_count += 1
            else:
                fail_count += 1
    
    return success_count, fail_count


def main():
    global selected_downloader, concurrent_fragments
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Download SharePoint/Teams lecture videos")
    parser.add_argument('--retry', action='store_true', 
                        help='Retry only previously failed downloads')
    parser.add_argument('--force', action='store_true',
                        help='Force re-download even if file exists (delete first)')
    parser.add_argument('-p', '--parallel', type=int, default=1, metavar='N',
                        help='Number of parallel downloads (default: 1). WARNING: Use 1-2 max to avoid rate limiting (429 errors).')
    parser.add_argument('-d', '--downloader', choices=['auto', 'ffmpeg', 'ytdlp'],
                        default='auto',
                        help='Download method: auto (interactive prompt), ffmpeg, or ytdlp')
    parser.add_argument('-f', '--fragments', type=int, default=4, metavar='N',
                        help='Number of concurrent fragment downloads for yt-dlp (default: 4)')
    args = parser.parse_args()

    
    print("=" * 60)
    print("  📹 SharePoint/Teams Lecture Video Downloader")
    if args.retry:
        print("  🔄 RETRY MODE - Only attempting failed downloads")
    if args.parallel > 1:
        print(f"  🚀 PARALLEL MODE - {args.parallel} concurrent downloads")
        print(f"  ⚠️  WARNING: High parallel count may cause 429 errors")
    print(f"  ⏳ Rate limiting: {DELAY_BETWEEN_DOWNLOADS}s delay between downloads")
    print("=" * 60)
    
    # Check if notifications are available
    if ENABLE_NOTIFICATIONS and not NOTIFICATIONS_AVAILABLE:
        print("\n💡 Tip: Install 'plyer' for desktop notifications:")
        print("   pip install plyer")
    
    # Load manifest
    manifest = load_manifest()
    if manifest is None:
        return
    
    # Ensure all folders exist from manifest
    ensure_all_folders_from_manifest(manifest)
    
    # Select downloader (command-line or interactive)
    if args.downloader == 'auto':
        # Interactive prompt
        downloader, num_fragments = select_downloader()
        if downloader is None:
            print("❌ No downloader available. Exiting.")
            return
    elif args.downloader == 'ytdlp':
        if not check_ytdlp_available():
            print("❌ yt-dlp is not installed. Install with: pip install yt-dlp")
            return
        selected_downloader = "ytdlp"
        concurrent_fragments = max(1, min(16, args.fragments))
        print(f"\n✅ Using yt-dlp with {concurrent_fragments} parallel fragment downloads")
    else:  # ffmpeg
        if not check_ffmpeg_available():
            print("❌ ffmpeg is not installed. Please install ffmpeg.")
            return
        selected_downloader = "ffmpeg"
        concurrent_fragments = 1
        print("\n✅ Using ffmpeg for downloads")


    # Handle retry mode
    retry_map = {}  # subject -> list of video dicts to retry (with name and optionally fresh url)
    if args.retry:
        previous_failures = load_failed_downloads()
        if not previous_failures:
            print("\n✅ No previous failures found! Nothing to retry.")
            return
        
        print(f"\n📋 Found {len(previous_failures)} failed downloads to retry:")
        for fail in previous_failures:
            subj = fail.get('subject', 'Unknown')
            name = fail.get('name', 'Unknown')
            fresh_url = fail.get('url', '')  # Check for fresh URL in failed_downloads.json
            if fresh_url:
                print(f"   - {subj}: {name} (using fresh URL)")
            else:
                print(f"   - {subj}: {name}")
            if subj not in retry_map:
                retry_map[subj] = []
            # Store both name and fresh_url for retry
            retry_map[subj].append({'name': name, 'url': fresh_url})
        
        # Clear the global failed list for this run
        failed_downloads.clear()
    
    # Select subject (or use retry subjects)
    if args.retry:
        subjects_to_process = list(retry_map.keys())
    else:
        subject = select_subject(manifest)
        if subject is None:
            return
        subjects_to_process = list(manifest.keys()) if subject == "ALL" else [subject]
    
    # Download
    total_success = 0
    total_fail = 0
    start_time = time.time()
    
    for subj in subjects_to_process:
        if subj not in manifest or not manifest[subj]:
            continue
        
        if args.retry:
            # Build videos list with fresh URLs from failed_downloads if available
            retry_data = retry_map.get(subj, [])
            retry_names = [r['name'] for r in retry_data]
            
            # Create a modified video list that uses fresh URLs where available
            videos_to_use = []
            for video in manifest[subj]:
                video_name = video.get('name', '')
                if video_name in retry_names:
                    # Find the retry entry with potential fresh URL
                    for r in retry_data:
                        if r['name'] == video_name:
                            if r.get('url'):  # Use fresh URL from failed_downloads.json
                                videos_to_use.append({'name': video_name, 'url': r['url']})
                            else:  # Fall back to manifest URL
                                videos_to_use.append(video)
                            break
            
            success, fail = download_subject(subj, videos_to_use, retry_only=retry_names, parallel_workers=args.parallel)
        else:
            success, fail = download_subject(subj, manifest[subj], retry_only=None, parallel_workers=args.parallel)
        total_success += success
        total_fail += fail
    
    total_time = time.time() - start_time
    
    # Save any failed downloads
    if total_fail > 0:
        save_failed_downloads()
        # Send failure notification
        send_notification(
            "Download Incomplete",
            f"✅ {total_success} successful\n❌ {total_fail} failed\nCheck failed_downloads.json"
        )
    elif args.retry and FAILED_LOG.exists():
        # If retry was successful, remove the failed log
        FAILED_LOG.unlink()
        print("\n🎉 All retries successful! Cleared failed downloads log.")
        send_notification(
            "Retry Successful! 🎉",
            f"All {total_success} videos downloaded successfully"
        )
    else:
        # Send success notification
        send_notification(
            "Download Complete! ✅",
            f"Successfully downloaded {total_success} videos in {total_time/60:.1f} minutes"
        )
    
    # Summary
    print("\n" + "=" * 60)
    print("  📊 Download Summary")
    print("=" * 60)
    print(f"  ✅ Successful: {total_success}")
    print(f"  ❌ Failed: {total_fail}")
    print(f"  ⏱️ Total time: {total_time/60:.1f} minutes")
    if total_fail > 0:
        print(f"\n  💡 To retry failed downloads:")
        print(f"     1. Check {FAILED_LOG}")
        print(f"     2. Update URLs if expired")
        print(f"     3. Run: python download_lectures.py --retry")
    print("=" * 60)


if __name__ == "__main__":
    main()
