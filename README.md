# 📹 SharePoint/Teams Lecture Video Downloader

A robust Python script to download lecture recordings from SharePoint/Microsoft Teams using videomanifest URLs. Features include parallel downloads, automatic retry, duration validation, and comprehensive error handling.

---

## 🚀 Features

- ✅ **Parallel Downloads**: Download multiple videos simultaneously for faster completion
- ✅ **Automatic Retry**: Failed downloads are logged and can be retried easily
- ✅ **Duration Validation**: Ensures downloaded videos match expected length
- ✅ **Auto Folder Creation**: Automatically creates subject folders from JSON configuration
- ✅ **Progress Tracking**: Real-time progress updates with clear status messages
- ✅ **Error Recovery**: Robust error handling with detailed failure logs
- ✅ **Notification System**: Desktop notifications for download completion/failures
- ✅ **URL Expiry Handling**: Clear documentation for managing expired URLs

---

## 📋 Prerequisites

### 1. Install Python
- **Python 3.8 or higher** is required
- Download from: https://www.python.org/downloads/
- During installation, **check "Add Python to PATH"**

### 2. Install FFmpeg

FFmpeg is required for video processing.

#### Windows:
```bash
# Using Chocolatey (recommended)
choco install ffmpeg

# OR download manually:
# 1. Download from https://github.com/BtbN/FFmpeg-Builds/releases
# 2. Extract to C:\ffmpeg
# 3. Add C:\ffmpeg\bin to System PATH
```

#### macOS:
```bash
brew install ffmpeg
```

#### Linux:
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# Fedora
sudo dnf install ffmpeg

# Arch Linux
sudo pacman -S ffmpeg
```

**Verify FFmpeg Installation:**
```bash
ffmpeg -version
```

### 3. Install Required Python Packages

```bash
cd scripts
pip install -r requirements.txt
```

---

## 📁 Project Structure

```
IITP/
├── README.md                          # This file
├── scripts/
│   ├── download_lectures.py           # Main download script
│   ├── manifest_urls.json             # Your video URLs configuration
│   ├── manifest_urls.example.json     # Example configuration
│   ├── failed_downloads.json          # Auto-generated failure log
│   └── requirements.txt               # Python dependencies
├── AML/
│   └── Lectures/                      # Auto-created
├── DAA/
│   └── Lectures/                      # Auto-created
├── Prob&Stat/
│   └── Lectures/                      # Auto-created
└── [Other Subject Folders]/
    └── Lectures/
```

---

## ⚙️ Configuration

### Step 1: Create Your Configuration File

Copy the example and customize it:

```bash
cd scripts
cp manifest_urls.example.json manifest_urls.json
```

### Step 2: Edit `manifest_urls.json`

```json
{
  "AML": [
    {
      "name": "Lecture_01_Introduction",
      "url": "https://centralindia1-mediap.svc.ms/transform/videomanifest?provider=spo&inputFormat=mp4..."
    },
    {
      "name": "Lecture_02_Linear_Regression",
      "url": "https://centralindia1-mediap.svc.ms/transform/videomanifest?provider=spo&inputFormat=mp4..."
    }
  ],
  "DAA": [
    {
      "name": "Lecture_01_Complexity",
      "url": "https://centralindia1-mediap.svc.ms/transform/videomanifest?provider=spo&inputFormat=mp4..."
    }
  ],
  "Prob&Stat": [],
  "AdvanceCyberSecurity": []
}
```

### Step 3: Get videomanifest URLs

#### Method 1: From Microsoft Teams
1. Open Teams → Go to your class channel
2. Find the recording in **Files** tab
3. Right-click the video → **Open in SharePoint**
4. In SharePoint, click **Download** (don't actually download)
5. Open **Browser Developer Tools** (F12)
6. Go to **Network** tab
7. Look for requests containing `videomanifest`
8. Copy the **full URL** (it should start with `https://` and contain `videomanifest`)

#### Method 2: From SharePoint Directly
1. Navigate to SharePoint where videos are stored
2. Click on a video to open the player
3. Open **Developer Tools** (F12) → **Network** tab
4. Refresh the page
5. Filter by `videomanifest`
6. Copy the request URL

**Important:** URLs expire after some time (typically hours to days). If you get authentication errors, you'll need to fetch fresh URLs.

---

## 🎯 Usage

### Basic Usage (Sequential Downloads - RECOMMENDED)

**⚠️ Important: Use sequential downloads to avoid rate limiting (429 errors)**

```bash
cd scripts
python download_lectures.py
```

The script will:
1. Show you a list of subjects with videos
2. Ask you to select which subject to download
3. Download videos **one by one with delays** to avoid server rate limiting

### Parallel Downloads (Use with Caution)

**⚠️ WARNING:** SharePoint/Teams servers rate-limit requests. Using parallel downloads may result in **HTTP 429 (Too Many Requests)** errors.

```bash
# Only use 1-2 parallel downloads maximum
python download_lectures.py --parallel 1

# NOT recommended - will likely cause 429 errors
python download_lectures.py --parallel 3
```

**Rate Limiting:**
- The script automatically adds a **3-second delay** between each download
- On 429 errors, it waits **30 seconds** and retries automatically
- **Recommended:** Use sequential mode (no --parallel flag) for reliability

### Download All Subjects

```bash
python download_lectures.py
# Select option 0 when prompted

# With parallel downloads
python download_lectures.py --parallel 3
# Select option 0
```

### Retry Failed Downloads

If some downloads fail:

```bash
# Sequential retry
python download_lectures.py --retry

# Parallel retry (faster)
python download_lectures.py --retry --parallel 3
```

The script will automatically:
- Load failed downloads from `failed_downloads.json`
- Retry only those videos
- Clear the log if all succeed

---

## ⏱️ URL Expiry & Batch Size

### Understanding URL Expiry

SharePoint/Teams videomanifest URLs typically expire after:
- **6-24 hours** (most common)
- Sometimes up to **48 hours**

**Symptoms of expired URLs:**
- `403 Forbidden` errors
- `401 Unauthorized` errors
- `Token expired` messages

### Recommended Batch Sizes

Based on typical URL expiry times:

| Internet Speed | Videos per Batch | Parallel Workers | Estimated Time |
|----------------|------------------|------------------|----------------|
| Slow (1-5 Mbps) | 5-10 videos | 1-2 | 2-4 hours |
| Medium (10-50 Mbps) | 10-20 videos | 3-5 | 1-2 hours |
| Fast (50+ Mbps) | 20-30 videos | 5-8 | 30-60 min |

**Best Practice:**
1. Start with **10-15 videos** in your first batch
2. Use `--parallel 3` for balanced performance
3. If URLs expire, fetch fresh ones and retry
4. For many lectures, split into multiple sessions

### Handling Expired URLs

If you encounter authentication errors:

1. **Check `failed_downloads.json`:**
```json
{
  "timestamp": "2025-12-08T10:30:00",
  "failed": [
    {
      "subject": "AML",
      "name": "Lecture_03",
      "url": "",
      "error": "403 Forbidden"
    }
  ]
}
```

2. **Fetch fresh URLs** for failed videos (see Step 3 in Configuration)

3. **Update `failed_downloads.json`:**
```json
{
  "timestamp": "2025-12-08T10:30:00",
  "failed": [
    {
      "subject": "AML",
      "name": "Lecture_03",
      "url": "PASTE_FRESH_URL_HERE",
      "error": "403 Forbidden"
    }
  ]
}
```

4. **Run retry:**
```bash
python download_lectures.py --retry --parallel 3
```

---

## 🔔 Notifications

The script automatically sends desktop notifications for:

- ✅ **Download completion** (with success count)
- ❌ **Download failures** (with failure count)
- 🎉 **Successful retry operations**

### Enable Notifications

**Windows:** Works automatically (uses Windows 10/11 notifications)

**macOS/Linux:** Install additional package:
```bash
pip install plyer
```

---

## 🛡️ Error Handling & Recovery

### Automatic Error Recovery

The script includes multiple recovery mechanisms:

1. **Codec Copy Failure**: Automatically retries with re-encoding
2. **Network Timeouts**: Configurable timeout with retry
3. **Partial Downloads**: Detects and removes incomplete files
4. **Corrupted Videos**: Validates video length after download

### Duration Validation

Every downloaded video is validated:

```
Expected: 01:25:30 (from metadata)
Downloaded: 01:25:28 (actual file)
Status: ✅ Valid (within 2-second tolerance)
```

If validation fails:
- Video is marked as failed
- Re-download is triggered automatically
- Detailed error is logged

### Manual Recovery

If automatic recovery fails:

```bash
# 1. Check failed downloads
cat scripts/failed_downloads.json

# 2. Delete corrupted files manually (if needed)
rm "AML/Lectures/Lecture_03.mp4"

# 3. Retry with fresh URL
python download_lectures.py --retry
```

---

## 📊 Output Examples

### Successful Download
```
==================================================
📖 Subject: AML
   Videos to download: 5
   Destination: D:\IITP\AML\Lectures
   🚀 Parallel downloads: 3
==================================================

🎬 Downloading: Lecture_01_Introduction.mp4
   To: D:\IITP\AML\Lectures
   Expected duration: 01:25:30
   Downloading... ████████████████ 100%
   ✅ Downloaded (1.2 GB)
   📏 Validating duration...
   ✅ Duration valid: 01:25:28 (within tolerance)

✅ Successfully downloaded: Lecture_01_Introduction.mp4

============================================================
  📊 Download Summary
============================================================
  ✅ Successful: 5
  ❌ Failed: 0
  📹 Total size: 6.8 GB
  ⏱️ Total time: 45 minutes
============================================================
```

### Failed Download
```
🎬 Downloading: Lecture_03.mp4
   To: D:\IITP\AML\Lectures
❌ Failed to download: Lecture_03.mp4
   Error: HTTP Error 403: Forbidden (Token may have expired)

📝 Failed downloads saved to: D:\IITP\scripts\failed_downloads.json

============================================================
  📊 Download Summary
============================================================
  ✅ Successful: 4
  ❌ Failed: 1
  
  💡 To retry failed downloads, run:
     python download_lectures.py --retry
============================================================
```

---

## 🐛 Troubleshooting

### Issue: "ffmpeg not found"
**Solution:**
```bash
# Verify installation
ffmpeg -version

# Add to PATH (Windows)
# System Properties → Environment Variables → Path → Add ffmpeg bin folder

# Reinstall (macOS)
brew reinstall ffmpeg
```

### Issue: "403 Forbidden" or "401 Unauthorized" or "429 Too Many Requests"

**403/401 Solution:** URLs have expired
1. Fetch fresh videomanifest URLs (see Configuration Step 3)
2. Update `manifest_urls.json` or `failed_downloads.json`
3. Run `python download_lectures.py --retry`

**429 Solution:** Server rate limiting (too many requests)
1. **Use sequential downloads:** Remove `--parallel` flag
2. **Reduce parallel count:** Use `--parallel 1` only
3. **Wait longer:** The script auto-waits 30 seconds on 429 errors
4. **Download in smaller batches:** 5-10 videos at a time
5. **Try again later:** Server may be temporarily overloaded

```bash
# RECOMMENDED for avoiding 429 errors
python download_lectures.py

# If you must use parallel, use only 1-2
python download_lectures.py --parallel 1
```

The script now includes:
- **3-second delay** between each download
- **Automatic retry** with 30-second wait on 429 errors
- **Relaxed duration validation** (10-second tolerance)

### Issue: "Duration mismatch" or corrupted video
**Solution:** Re-download with re-encoding
```bash
# The script automatically retries with re-encoding
# If that fails, manually:
rm "path/to/corrupted/video.mp4"
python download_lectures.py --retry
```

### Issue: "SSL Certificate Error"
**Solution:**
```bash
# Update CA certificates
pip install --upgrade certifi

# OR use environment variable (not recommended)
export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
```

### Issue: Download is too slow
**Solution:**
1. Reduce parallel workers: `--parallel 1`
2. Check your internet connection
3. Try downloading during off-peak hours
4. Verify no bandwidth throttling on your network

### Issue: Out of disk space
**Solution:**
```bash
# Check available space
df -h  # Linux/macOS
wmic logicaldisk get size,freespace,caption  # Windows

# Free up space or change destination
# Edit BASE_DIR in download_lectures.py
```

---

## 📝 Advanced Configuration

### Custom Timeout

Edit `download_lectures.py`:

```python
# Default timeout calculation:
# timeout = max(600, expected_duration + 300)  # minimum 10 min, or video length + 5 min

# For slower connections, increase buffer:
timeout = max(900, expected_duration + 600)  # minimum 15 min, or video length + 10 min
```

### Custom Validation Tolerance

```python
# Default: 2 seconds tolerance
DURATION_TOLERANCE = 2

# For stricter validation:
DURATION_TOLERANCE = 1

# For more lenient validation:
DURATION_TOLERANCE = 5
```

### Disable Notifications

```python
# Set to False to disable
ENABLE_NOTIFICATIONS = False
```

---

## 📄 Example Configuration Files

### `manifest_urls.example.json`
```json
{
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
```

### `requirements.txt`
```
plyer>=2.1.0
```

---

## 🤝 Contributing

Found a bug or want to add a feature? Contributions are welcome!

---

## 📜 License

This project is provided as-is for educational purposes.

---

## ⚠️ Disclaimer

- This script is for **personal educational use only**
- Ensure you have the **right to download** the videos
- Respect **copyright and usage policies** of your institution
- URLs are **temporary** and **expire** - fetch fresh ones as needed
- **SharePoint/Teams policies** may limit concurrent downloads

---

## 🆘 Support

If you encounter issues:

1. Check the **Troubleshooting** section above
2. Review `failed_downloads.json` for specific errors
3. Verify FFmpeg is properly installed
4. Ensure URLs are not expired
5. Try reducing parallel workers

---

## 📞 Quick Reference

| Command | Description |
|---------|-------------|
| `python download_lectures.py` | Basic sequential download |
| `python download_lectures.py --parallel 3` | Download 3 videos simultaneously |
| `python download_lectures.py --retry` | Retry failed downloads |
| `python download_lectures.py --retry -p 3` | Retry with parallel downloads |
| `ffmpeg -version` | Check FFmpeg installation |
| `pip install -r requirements.txt` | Install dependencies |

---

**Happy Downloading! 🎓📹**
