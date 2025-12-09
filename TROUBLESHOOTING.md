# 🔧 Troubleshooting & FAQ

## Common Issues

### 1. FFmpeg Not Found

**Symptoms:**
```
❌ ffmpeg not found! Please install ffmpeg and add it to PATH.
```

**Solutions:**

**Windows:**
```bash
# Option 1: Using Chocolatey (Recommended)
choco install ffmpeg

# Option 2: Manual Installation
# 1. Download from https://github.com/BtbN/FFmpeg-Builds/releases
# 2. Extract to C:\ffmpeg
# 3. Add C:\ffmpeg\bin to System PATH:
#    - Search "Environment Variables" in Start Menu
#    - Edit "Path" in System Variables
#    - Add new entry: C:\ffmpeg\bin
#    - Restart terminal
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt update && sudo apt install ffmpeg  # Ubuntu/Debian
sudo dnf install ffmpeg                      # Fedora
sudo pacman -S ffmpeg                        # Arch
```

**Verify Installation:**
```bash
ffmpeg -version
which ffmpeg  # Linux/macOS
where ffmpeg  # Windows
```

---

### 2. URL Expiration (403/401 Errors)

**Symptoms:**
```
❌ Failed to download: Lecture_03.mp4
   Error: HTTP Error 403: Forbidden (Token may have expired)
```

**Why it happens:**
- SharePoint URLs expire after 6-24 hours
- Authentication tokens become invalid

**Solution:**

1. **Check failed downloads:**
```bash
cat scripts/failed_downloads.json
```

2. **Get fresh URLs** (see QUICKSTART.md for detailed steps)

3. **Update the failed_downloads.json:**
```json
{
  "timestamp": "2025-12-08T10:30:00",
  "failed": [
    {
      "subject": "AML",
      "name": "Lecture_03",
      "url": "PASTE_FRESH_VIDEOMANIFEST_URL_HERE",
      "error": "403 Forbidden"
    }
  ]
}
```

4. **Retry:**
```bash
python download_lectures.py --retry --parallel 3
```

**Prevention:**
- Download in batches of 10-20 videos
- Complete each batch within 12 hours
- Use `--parallel 3-5` for faster completion

---

### 3. Duration Validation Failed

**Symptoms:**
```
❌ Validation failed: Duration mismatch: expected 01:25:30, got 01:20:15 (diff: 315.0s)
```

**Why it happens:**
- Network interruption during download
- Corrupted stream segments
- Server-side issues

**Solution:**

The script **automatically retries** with re-encoding. If that fails:

1. **Manual retry:**
```bash
# The script already logged it as failed
python download_lectures.py --retry
```

2. **Adjust tolerance** (if videos are consistently off by a few seconds):

Edit `download_lectures.py`:
```python
DURATION_TOLERANCE = 5  # Allow 5 seconds difference (default is 2)
```

3. **Force fresh download:**
```bash
# Delete the file and retry
rm "path/to/video.mp4"
python download_lectures.py --retry
```

---

### 4. Slow Download Speeds

**Symptoms:**
- Downloads taking too long
- Network bottleneck

**Solutions:**

1. **Reduce parallel downloads:**
```bash
python download_lectures.py --parallel 1  # Sequential
```

2. **Check your internet speed:**
```bash
# Run a speed test
speedtest-cli  # Install: pip install speedtest-cli
```

3. **Download during off-peak hours:**
- Early morning (2-6 AM)
- Late night (11 PM - 2 AM)

4. **Recommended settings by internet speed:**

| Speed | Parallel Workers | Expected Time (per GB) |
|-------|------------------|------------------------|
| 1-5 Mbps | 1-2 | 30-45 min |
| 10-25 Mbps | 2-3 | 10-15 min |
| 50+ Mbps | 3-5 | 3-5 min |

---

### 5. Out of Disk Space

**Symptoms:**
```
❌ Error downloading: [Errno 28] No space left on device
```

**Solutions:**

1. **Check available space:**
```bash
# Linux/macOS
df -h

# Windows (PowerShell)
Get-PSDrive
```

2. **Change download location:**

Edit `download_lectures.py`:
```python
# Change this line (around line 24)
BASE_DIR = SCRIPT_DIR.parent  # Default: d:\IITP

# To custom location:
BASE_DIR = Path("E:/Lectures")  # Your drive with more space
```

3. **Clean up old downloads:**
```bash
# Delete test downloads
rm -rf test_downloads/

# Clear backups
rm -rf backups/
```

**Space estimates:**
- 1 hour lecture: ~500 MB - 1.5 GB
- Full semester (40 lectures): ~40-60 GB

---

### 6. Notifications Not Working

**Symptoms:**
- No desktop notifications appear

**Solutions:**

1. **Install notification library:**
```bash
pip install plyer
```

2. **Check notification settings (Windows):**
- Settings → System → Notifications
- Allow notifications for Python

3. **Disable notifications** (if not needed):

Edit `download_lectures.py`:
```python
# Change this line (around line 31)
ENABLE_NOTIFICATIONS = False
```

---

### 7. SSL Certificate Errors

**Symptoms:**
```
SSL: CERTIFICATE_VERIFY_FAILED
```

**Solutions:**

1. **Update CA certificates:**
```bash
pip install --upgrade certifi
```

2. **Update Python:**
```bash
python --version  # Should be 3.8+
# Download latest from python.org
```

3. **Temporary workaround** (not recommended for production):
```bash
# Linux/macOS
export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

# Windows - not recommended, fix certificate issue instead
```

---

### 8. Script Hangs or Freezes

**Symptoms:**
- Script appears stuck
- No progress for long time

**Solutions:**

1. **Check if download is actually running:**
```bash
# Open task manager and look for ffmpeg process
# It should show network activity
```

2. **Timeout is too short for large videos:**

The script calculates timeout as:
```
timeout = max(600, video_duration + 300)  # 10 min minimum or video length + 5 min
```

For very slow internet, edit `download_lectures.py`:
```python
# Find download_video function, around line 180
timeout_seconds = max(1800, int(expected_duration) + 900)  # 30 min minimum
```

3. **Kill and retry:**
```bash
# Ctrl+C to stop
# Then retry
python download_lectures.py --retry
```

---

### 9. "Module not found" Errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'plyer'
```

**Solution:**
```bash
cd scripts
pip install -r requirements.txt

# Or individually:
pip install plyer
```

**If using virtual environment:**
```bash
# Activate venv first
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Then install
pip install -r requirements.txt
```

---

### 10. File Already Exists

**Symptoms:**
```
⏭️ Skipping (already exists): Lecture_01.mp4
```

**This is normal behavior** - the script skips already downloaded files.

**To force re-download:**
1. **Delete the file manually:**
```bash
rm "AML/Lectures/Lecture_01.mp4"
python download_lectures.py
```

2. **Or mark as failed and retry:**
Edit `failed_downloads.json`:
```json
{
  "failed": [
    {
      "subject": "AML",
      "name": "Lecture_01",
      "url": "",
      "error": "Re-download requested"
    }
  ]
}
```

Then:
```bash
python download_lectures.py --retry
```

---

## FAQ

### Q: How long do URLs last?
**A:** Typically 6-24 hours, sometimes up to 48 hours. Download in batches to avoid expiration.

### Q: What's the best batch size?
**A:** 10-20 videos per session is recommended. Adjust based on your internet speed.

### Q: Can I pause and resume?
**A:** Yes! Just press Ctrl+C to stop. Already downloaded videos are skipped on next run.

### Q: What if my internet disconnects?
**A:** The script validates each video. Failed/incomplete downloads are logged in `failed_downloads.json`. Just run `--retry` when back online.

### Q: How much storage do I need?
**A:** ~1-2 GB per hour of video. A full semester (40 lectures, 1 hour each) = ~40-60 GB.

### Q: Can I download multiple subjects at once?
**A:** Yes! Select option "0" when prompted, or edit the script to set subjects.

### Q: Is there a download limit?
**A:** SharePoint may throttle excessive concurrent downloads. Use `--parallel 3-5` max.

### Q: Videos are corrupted/won't play
**A:** The script validates duration automatically. If validation passes but video won't play, try:
```bash
# Re-encode the video
ffmpeg -i input.mp4 -c:v libx264 -c:a aac output.mp4
```

### Q: Can I change video quality?
**A:** The script downloads the highest available quality from the manifest. To compress:
```bash
ffmpeg -i input.mp4 -vf scale=-2:720 -c:v libx264 -crf 23 -c:a aac output.mp4
```

### Q: How to download from command line without prompt?
**A:** Edit the script or modify the select_subject function to return a specific subject.

---

## Performance Tips

1. **Optimal parallel downloads:** 3-5 workers
2. **Use SSD** for faster write speeds
3. **Close bandwidth-heavy apps** during download
4. **Use wired connection** instead of WiFi
5. **Download during off-peak hours**

---

## Getting Help

If none of these solutions work:

1. **Check the error message** in `failed_downloads.json`
2. **Verify ffmpeg** is working: `ffmpeg -version`
3. **Test with one video** first: Use small batch
4. **Check SharePoint status**: Sometimes server-side issues occur
5. **Review logs**: Detailed errors are printed during download

---

## Reporting Issues

When reporting issues, include:
- Python version: `python --version`
- FFmpeg version: `ffmpeg -version`
- Operating system
- Error message from console
- Content of `failed_downloads.json`
- Sample URL (remove sensitive tokens)

---

**Still stuck?** Check the main [README.md](README.md) for complete documentation.
