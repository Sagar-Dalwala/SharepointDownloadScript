#!/usr/bin/env python3
"""
SharePoint/Teams Lecture Video Downloader

This script automates downloading lecture recordings from SharePoint/Teams
using videomanifest URLs and ffmpeg.

Usage:
    python download_lectures.py
    
The script reads URLs from manifest_urls.json in the same directory.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Configuration
SCRIPT_DIR = Path(__file__).parent
MANIFEST_FILE = SCRIPT_DIR / "manifest_urls.json"
BASE_DIR = SCRIPT_DIR.parent  # d:\IITP


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


def download_video(url: str, output_path: Path, use_reencode: bool = False) -> bool:
    """
    Download video using ffmpeg.
    
    Args:
        url: The trimmed videomanifest URL
        output_path: Full path for the output MP4 file
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
                return download_video(url, output_path, use_reencode=True)
            else:
                print(f"❌ Failed to download: {output_path.name}")
                print(f"   Error: {result.stderr[:500] if result.stderr else 'Unknown error'}")
                return False
                
    except FileNotFoundError:
        print("❌ ffmpeg not found! Please install ffmpeg and add it to PATH.")
        print("   Download from: https://ffmpeg.org/download.html")
        return False
    except Exception as e:
        print(f"❌ Error downloading {output_path.name}: {e}")
        return False


def download_subject(subject: str, videos: list) -> tuple:
    """Download all videos for a subject."""
    lectures_dir = ensure_lectures_folder(subject)
    
    success_count = 0
    fail_count = 0
    
    print(f"\n{'='*50}")
    print(f"📖 Subject: {subject}")
    print(f"   Videos to download: {len(videos)}")
    print(f"   Destination: {lectures_dir}")
    print(f"{'='*50}")
    
    for video in videos:
        name = video.get('name', 'Unknown')
        url = video.get('url', '')
        
        if not url or url == "PASTE_YOUR_VIDEOMANIFEST_URL_HERE":
            print(f"⏭️ Skipping {name}: No valid URL")
            continue
        
        # Ensure name ends with .mp4
        if not name.endswith('.mp4'):
            name = f"{name}.mp4"
        
        output_path = lectures_dir / name
        
        # Trim the URL
        trimmed_url = trim_url(url)
        
        # Download
        if download_video(trimmed_url, output_path):
            success_count += 1
        else:
            fail_count += 1
    
    return success_count, fail_count


def main():
    print("=" * 60)
    print("  📹 SharePoint/Teams Lecture Video Downloader")
    print("=" * 60)
    
    # Load manifest
    manifest = load_manifest()
    if manifest is None:
        return
    
    # Select subject
    subject = select_subject(manifest)
    if subject is None:
        return
    
    # Download
    total_success = 0
    total_fail = 0
    
    if subject == "ALL":
        for subj, videos in manifest.items():
            if videos:
                success, fail = download_subject(subj, videos)
                total_success += success
                total_fail += fail
    else:
        total_success, total_fail = download_subject(subject, manifest[subject])
    
    # Summary
    print("\n" + "=" * 60)
    print("  📊 Download Summary")
    print("=" * 60)
    print(f"  ✅ Successful: {total_success}")
    print(f"  ❌ Failed: {total_fail}")
    print("=" * 60)


if __name__ == "__main__":
    main()
