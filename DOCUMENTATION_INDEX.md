# 📚 Complete Documentation Index

Welcome to the SharePoint/Teams Lecture Video Downloader! This index will guide you to the right documentation.

---

## 🎯 Getting Started

### New User? Start Here:
1. **[QUICKSTART.md](QUICKSTART.md)** - 5-minute setup guide
   - Install prerequisites
   - Basic configuration
   - Run your first download

### Need Detailed Instructions?
2. **[README.md](README.md)** - Complete documentation
   - All features explained
   - Advanced usage
   - Configuration options
   - Command-line arguments

---

## 🔧 Having Problems?

3. **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Solutions to common issues
   - FFmpeg not found
   - URL expiration
   - Download failures
   - Performance issues
   - Complete FAQ section

---

## 📁 File Reference

### Configuration Files

| File | Purpose | Location |
|------|---------|----------|
| `manifest_urls.json` | Your video URLs (create from example) | `scripts/` |
| `manifest_urls.example.json` | Template with instructions | `scripts/` |
| `failed_downloads.json` | Auto-generated failure log | `scripts/` |
| `requirements.txt` | Python dependencies | `scripts/` |

### Script Files

| File | Purpose |
|------|---------|
| `download_lectures.py` | Main download script |
| `test_download.py` | Testing utility |

---

## 🎓 Feature Overview

### ✅ What This Script Does

- **Parallel Downloads**: Download multiple videos simultaneously (3-5x faster)
- **Auto Folder Creation**: Creates subject folders automatically from JSON
- **Duration Validation**: Ensures videos are complete and not corrupted
- **Smart Retry**: Automatically retries failed downloads with different methods
- **Error Recovery**: Handles network issues, timeouts, and authentication errors
- **Desktop Notifications**: Alerts you when downloads complete or fail
- **Progress Tracking**: Real-time status updates for each download
- **URL Expiry Handling**: Clear instructions for managing expired URLs

### ⚙️ Command Options

```bash
# Basic usage
python download_lectures.py

# Parallel downloads (faster)
python download_lectures.py --parallel 3

# Retry failed downloads
python download_lectures.py --retry

# Retry with parallel
python download_lectures.py --retry --parallel 5
```

---

## 📊 Workflow Overview

### Step-by-Step Process

```
1. Setup
   ├── Install FFmpeg
   ├── Install Python packages
   └── Create manifest_urls.json

2. Get URLs
   ├── Open Teams/SharePoint
   ├── Use DevTools to capture videomanifest URLs
   └── Add to manifest_urls.json

3. Download
   ├── Run script with --parallel 3
   ├── Videos download with validation
   └── Failures logged to failed_downloads.json

4. Handle Failures (if any)
   ├── Check failed_downloads.json
   ├── Update with fresh URLs (if expired)
   └── Run with --retry flag

5. Enjoy!
   └── Videos organized in subject folders
```

---

## 🎯 Quick Command Reference

| Task | Command |
|------|---------|
| First time setup | `pip install -r requirements.txt` |
| Download all subjects | Select "0" when prompted |
| Download specific subject | Select subject number |
| Fast parallel download | `--parallel 3` |
| Retry failed | `--retry` |
| Check FFmpeg | `ffmpeg -version` |
| View failures | `cat failed_downloads.json` |

---

## ⚠️ Important Reminders

### URL Expiration
- SharePoint URLs expire in **6-24 hours**
- Download in **batches of 10-20 videos**
- Use **--parallel 3-5** to complete faster

### Storage Requirements
- **~1-2 GB per hour** of video
- **40 lectures** ≈ 40-60 GB
- Ensure sufficient disk space before starting

### Network Recommendations
- **Stable connection** required
- **Wired connection** preferred over WiFi
- **3-5 parallel downloads** for optimal speed
- **Off-peak hours** for faster downloads

### Best Practices
1. Test with **1-2 videos** first
2. Download in **small batches**
3. Keep **original URLs** in manifest
4. **Update URLs** promptly when they expire
5. **Monitor progress** during downloads

---

## 📖 Documentation Quick Links

| Document | Best For |
|----------|----------|
| [QUICKSTART.md](QUICKSTART.md) | Getting started in 5 minutes |
| [README.md](README.md) | Complete feature guide |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Solving problems |

---

## 🎓 Example Session

```bash
# 1. Setup (first time only)
cd scripts
pip install -r requirements.txt

# 2. Configure
cp manifest_urls.example.json manifest_urls.json
# Edit manifest_urls.json with your URLs

# 3. Download (fast mode)
python download_lectures.py --parallel 3
# Select subject or "0" for all

# 4. If any failures
python download_lectures.py --retry --parallel 3

# Done! Videos are in: ../[Subject]/Lectures/
```

---

## 🆘 Need Help?

1. **Quick issues**: Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. **Usage questions**: See [README.md](README.md)
3. **Setup problems**: Follow [QUICKSTART.md](QUICKSTART.md)
4. **Error messages**: Search in TROUBLESHOOTING.md

---

## 📈 Success Tips

### For Best Results:
- ✅ Use **stable internet connection**
- ✅ Download **10-20 videos** per batch
- ✅ Use **--parallel 3-5** for speed
- ✅ **Validate** URLs before batch downloads
- ✅ **Monitor** disk space during downloads
- ✅ Keep **backup** of manifest_urls.json

### Avoid:
- ❌ Downloading **too many** videos at once
- ❌ Using **expired URLs**
- ❌ **Too many** parallel workers (>8)
- ❌ Downloading on **unstable WiFi**
- ❌ Running out of **disk space** mid-download

---

## 🎉 You're All Set!

This documentation covers everything you need. Start with [QUICKSTART.md](QUICKSTART.md) and you'll be downloading in minutes!

**Happy Learning! 📹🎓**
