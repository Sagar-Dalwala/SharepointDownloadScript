#!/usr/bin/env python3
"""
SharePoint/Teams Lecture Video Downloader

This script automates downloading lecture recordings from SharePoint/Teams
using videomanifest URLs and ffmpeg.

Usage:
    python download_lectures.py                    # Normal download (sequential)
    python download_lectures.py --parallel 3      # Download 3 videos at once
    python download_lectures.py --retry           # Retry only failed downloads
    python download_lectures.py --retry -p 5      # Retry with 5 parallel downloads
    
The script reads URLs from manifest_urls.json in the same directory.
"""

import json
import os
import subprocess
import sys
import argparse
import threading
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
SCRIPT_DIR = Path(__file__).parent
MANIFEST_FILE = SCRIPT_DIR / "manifest_urls.json"
FAILED_LOG = SCRIPT_DIR / "failed_downloads.json"
BASE_DIR = SCRIPT_DIR.parent  # d:\IITP

# Global list to track failed downloads (thread-safe with lock)
failed_downloads = []
failed_downloads_lock = threading.Lock()


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
    """Create Lectures folder inside subject folder if it doesn't exist."""
    subject_dir = BASE_DIR / subject
    lectures_dir = subject_dir / "Lectures"
    
    if not subject_dir.exists():
        print(f"📁 Creating subject folder: {subject_dir}")
        subject_dir.mkdir(parents=True)
    
    if not lectures_dir.exists():
        print(f"📁 Creating Lectures folder: {lectures_dir}")
        lectures_dir.mkdir(parents=True)
    
    return lectures_dir


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


def download_video(url: str, output_path: Path, subject: str = "", name: str = "", original_url: str = "", use_reencode: bool = False) -> bool:
    """
    Download video using ffmpeg.
    
    Args:
        url: The trimmed videomanifest URL
        output_path: Full path for the output MP4 file
        subject: Subject name (for logging)
        name: Video name (for logging)
        original_url: Original full URL (for logging failed downloads)
        use_reencode: If True, re-encode instead of codec copy
    
    Returns:
        True if successful, False otherwise
    """
    if output_path.exists():
        print(f"⏭️ Skipping (already exists): {output_path.name}")
        return True
    
    if use_reencode:
        cmd = [
            'ffmpeg',
            '-i', url,
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-b:a', '128k',
            str(output_path)
        ]
    else:
        cmd = [
            'ffmpeg',
            '-i', url,
            '-codec', 'copy',
            str(output_path)
        ]
    
    print(f"\n🎬 Downloading: {output_path.name}")
    print(f"   To: {output_path.parent}")
    
    try:
        # Run ffmpeg
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ Successfully downloaded: {output_path.name}")
            return True
        else:
            # If codec copy failed, try re-encoding
            if not use_reencode:
                print(f"⚠️ Codec copy failed, trying re-encode...")
                return download_video(url, output_path, subject, name, original_url, use_reencode=True)
            else:
                error_msg = extract_ffmpeg_error(result.stderr)
                print(f"❌ Failed to download: {output_path.name}")
                print(f"   Error: {error_msg}")
                
                # Log the failure (thread-safe)
                with failed_downloads_lock:
                    failed_downloads.append({
                        "subject": subject,
                        "name": name,
                        "url": "",  # Empty placeholder - paste fresh URL here for retry
                        "error": error_msg
                    })
                return False
                
    except FileNotFoundError:
        print("❌ ffmpeg not found! Please install ffmpeg and add it to PATH.")
        print("   Download from: https://ffmpeg.org/download.html")
        return False
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error downloading {output_path.name}: {error_msg}")
        with failed_downloads_lock:
            failed_downloads.append({
                "subject": subject,
                "name": name,
                "url": "",  # Empty placeholder - paste fresh URL here for retry
                "error": error_msg
            })
        return False


def download_single_video(args):
    """
    Download a single video. Used as a worker function for parallel downloads.
    
    Args:
        args: tuple of (subject, video, lectures_dir, retry_only)
    
    Returns:
        tuple of (success: bool, video_name: str)
    """
    subject, video, lectures_dir, retry_only = args
    
    name = video.get('name', 'Unknown')
    url = video.get('url', '')
    
    if not url or url == "PASTE_YOUR_VIDEOMANIFEST_URL_HERE":
        print(f"⏭️ Skipping {name}: No valid URL")
        return (None, name)  # None = skipped
    
    # Store original name for logging
    original_name = name
    
    # Ensure name ends with .mp4
    if not name.endswith('.mp4'):
        name = f"{name}.mp4"
    
    output_path = lectures_dir / name
    
    # For retry mode, delete partial/failed files first
    if retry_only and output_path.exists():
        print(f"🗑️ Removing failed file for retry: {name}")
        output_path.unlink()
    
    # Trim the URL
    trimmed_url = trim_url(url)
    
    # Download (pass original URL for logging if it fails)
    success = download_video(trimmed_url, output_path, subject, original_name, url)
    return (success, original_name)


def download_subject(subject: str, videos: list, retry_only: list = None, parallel_workers: int = 1) -> tuple:
    """Download all videos for a subject.
    
    Args:
        subject: Subject name
        videos: List of video dicts with 'name' and 'url'
        retry_only: If provided, only download videos whose names are in this list
        parallel_workers: Number of parallel downloads (1 = sequential)
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
    print(f"{'='*50}")
    
    # Prepare arguments for each video
    download_args = [(subject, video, lectures_dir, retry_only) for video in videos_to_download]
    
    if parallel_workers > 1:
        # Parallel download mode
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
        # Sequential download mode (original behavior)
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
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Download SharePoint/Teams lecture videos")
    parser.add_argument('--retry', action='store_true', 
                        help='Retry only previously failed downloads')
    parser.add_argument('--force', action='store_true',
                        help='Force re-download even if file exists (delete first)')
    parser.add_argument('-p', '--parallel', type=int, default=1, metavar='N',
                        help='Number of parallel downloads (default: 1 = sequential). Use 3-5 for faster downloads.')
    args = parser.parse_args()
    
    print("=" * 60)
    print("  📹 SharePoint/Teams Lecture Video Downloader")
    if args.retry:
        print("  🔄 RETRY MODE - Only attempting failed downloads")
    if args.parallel > 1:
        print(f"  🚀 PARALLEL MODE - {args.parallel} concurrent downloads")
    print("=" * 60)
    
    # Load manifest
    manifest = load_manifest()
    if manifest is None:
        return
    
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
    
    # Save any failed downloads
    if total_fail > 0:
        save_failed_downloads()
    elif args.retry and FAILED_LOG.exists():
        # If retry was successful, remove the failed log
        FAILED_LOG.unlink()
        print("\n🎉 All retries successful! Cleared failed downloads log.")
    
    # Summary
    print("\n" + "=" * 60)
    print("  📊 Download Summary")
    print("=" * 60)
    print(f"  ✅ Successful: {total_success}")
    print(f"  ❌ Failed: {total_fail}")
    if total_fail > 0:
        print(f"\n  💡 To retry failed downloads, run:")
        print(f"     python download_lectures.py --retry")
    print("=" * 60)


if __name__ == "__main__":
    main()
