#!/usr/bin/env python3
"""
Setup Verification Script

Run this script to verify your environment is properly configured
before attempting to download videos.
"""

import sys
import subprocess
from pathlib import Path

def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def check_python():
    """Check Python version."""
    print("\n🐍 Python Version:")
    version = sys.version_info
    print(f"   {sys.version}")
    
    if version.major >= 3 and version.minor >= 8:
        print("   ✅ Python version is compatible (3.8+)")
        return True
    else:
        print("   ❌ Python 3.8 or higher required")
        print("   Download from: https://www.python.org/downloads/")
        return False

def check_ffmpeg():
    """Check if FFmpeg is installed."""
    print("\n📹 FFmpeg:")
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            # Get first line with version
            version_line = result.stdout.split('\n')[0]
            print(f"   {version_line}")
            print("   ✅ FFmpeg is installed and accessible")
            return True
        else:
            print("   ❌ FFmpeg found but not working properly")
            return False
            
    except FileNotFoundError:
        print("   ❌ FFmpeg not found in PATH")
        print("\n   Install FFmpeg:")
        print("   Windows: choco install ffmpeg")
        print("   macOS:   brew install ffmpeg")
        print("   Linux:   sudo apt install ffmpeg")
        return False
    except Exception as e:
        print(f"   ❌ Error checking FFmpeg: {e}")
        return False

def check_ffprobe():
    """Check if FFprobe is installed."""
    print("\n🔍 FFprobe:")
    try:
        result = subprocess.run(
            ['ffprobe', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("   ✅ FFprobe is installed (comes with FFmpeg)")
            return True
        else:
            print("   ⚠️ FFprobe found but not working properly")
            return False
            
    except FileNotFoundError:
        print("   ❌ FFprobe not found (should come with FFmpeg)")
        return False
    except Exception as e:
        print(f"   ⚠️ Error checking FFprobe: {e}")
        return False

def check_packages():
    """Check required Python packages."""
    print("\n📦 Python Packages:")
    
    all_ok = True
    
    # Check plyer (optional)
    try:
        import plyer
        print("   ✅ plyer (notifications) - installed")
    except ImportError:
        print("   ⚠️ plyer (notifications) - not installed (optional)")
        print("      Install with: pip install plyer")
    
    return all_ok

def check_files():
    """Check if required files exist."""
    print("\n📁 Required Files:")
    
    script_dir = Path(__file__).parent
    
    files_to_check = [
        ('download_lectures.py', True),
        ('manifest_urls.json', False),
        ('manifest_urls.example.json', True),
    ]
    
    all_ok = True
    
    for filename, required in files_to_check:
        filepath = script_dir / filename
        if filepath.exists():
            print(f"   ✅ {filename}")
        else:
            if required:
                print(f"   ❌ {filename} - REQUIRED")
                all_ok = False
            else:
                print(f"   ⚠️ {filename} - not found (create from example)")
    
    return all_ok

def check_manifest():
    """Check manifest_urls.json configuration."""
    print("\n⚙️ Configuration:")
    
    script_dir = Path(__file__).parent
    manifest_file = script_dir / "manifest_urls.json"
    
    if not manifest_file.exists():
        print("   ⚠️ manifest_urls.json not found")
        print("   Create it from manifest_urls.example.json")
        return False
    
    try:
        import json
        with open(manifest_file, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        total_videos = sum(len(videos) for videos in manifest.values())
        subjects_with_videos = [s for s, v in manifest.items() if v]
        
        print(f"   ✅ manifest_urls.json is valid JSON")
        print(f"   📊 {len(manifest)} subjects configured")
        print(f"   📹 {total_videos} total videos")
        
        if subjects_with_videos:
            print(f"\n   Subjects with videos:")
            for subject in subjects_with_videos:
                video_count = len(manifest[subject])
                print(f"     - {subject}: {video_count} videos")
        else:
            print("\n   ⚠️ No subjects have videos configured yet")
            print("   Add videomanifest URLs to manifest_urls.json")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"   ❌ Invalid JSON in manifest_urls.json")
        print(f"   Error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error reading manifest: {e}")
        return False

def check_disk_space():
    """Check available disk space."""
    print("\n💾 Disk Space:")
    
    try:
        import shutil
        script_dir = Path(__file__).parent.parent
        
        total, used, free = shutil.disk_usage(script_dir)
        
        free_gb = free / (1024 ** 3)
        total_gb = total / (1024 ** 3)
        used_percent = (used / total) * 100
        
        print(f"   Total: {total_gb:.1f} GB")
        print(f"   Used: {used_percent:.1f}%")
        print(f"   Free: {free_gb:.1f} GB")
        
        if free_gb < 10:
            print("   ⚠️ Low disk space! Need ~1-2 GB per hour of video")
            return False
        elif free_gb < 50:
            print("   ⚠️ Moderate disk space - download in small batches")
            return True
        else:
            print("   ✅ Sufficient disk space available")
            return True
            
    except Exception as e:
        print(f"   ⚠️ Could not check disk space: {e}")
        return True

def main():
    """Run all checks."""
    print_section("🔧 Environment Setup Verification")
    print("\nChecking your system configuration...\n")
    
    results = {
        "Python": check_python(),
        "FFmpeg": check_ffmpeg(),
        "FFprobe": check_ffprobe(),
        "Packages": check_packages(),
        "Files": check_files(),
        "Configuration": check_manifest(),
        "Disk Space": check_disk_space(),
    }
    
    # Summary
    print_section("📊 Verification Summary")
    
    all_passed = True
    for check, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("\n🎉 All checks passed! You're ready to download videos.")
        print("\n   Run: python download_lectures.py --parallel 3")
    else:
        print("\n⚠️ Some checks failed. Please fix the issues above.")
        print("\n   See QUICKSTART.md or README.md for help.")
    
    print("\n" + "=" * 60 + "\n")

if __name__ == "__main__":
    main()
