# 🔧 Dealing with 429 Rate Limiting Errors

## What is HTTP 429?

**HTTP 429 Too Many Requests** means the SharePoint/Teams server is rate-limiting your downloads. This happens when:
- Too many videos are downloaded too quickly
- Parallel downloads overwhelm the server
- You're making too many requests in a short time

---

## ✅ Solutions Implemented

The script now includes automatic handling:

### 1. **Rate Limiting Delay**
- **3-second delay** between each download
- Prevents overwhelming the server

### 2. **Automatic 429 Retry**
- Detects 429 errors automatically
- Waits **30 seconds** before retrying
- Up to **2 retry attempts** per video

### 3. **Relaxed Validation**
- Duration tolerance increased to **10 seconds**
- Prevents unnecessary re-downloads
- Keeps videos even with minor differences

### 4. **Sequential Mode Recommended**
- Default is now **sequential** (one at a time)
- Most reliable way to avoid 429 errors

---

## 🚀 How to Download Without 429 Errors

### Method 1: Sequential Downloads (RECOMMENDED)

```bash
cd scripts
python download_lectures.py
# Select your subject
# Wait patiently - downloads will complete one by one
```

**Pros:**
- ✅ No 429 errors
- ✅ Most reliable
- ✅ Automatic delays between downloads

**Cons:**
- ⏳ Slower (but reliable)

---

### Method 2: Test Single Video First

Use the simple test script to verify URLs work:

```bash
cd scripts
python simple_download.py "YOUR_URL_HERE" "test_video.mp4"
```

This performs a basic `ffmpeg -i URL -c copy output.mp4` with no extras.

**Example:**
```bash
python simple_download.py "https://centralindia1-mediap.svc.ms/transform/videomanifest?provider=spo..." "Lecture_09.mp4"
```

---

### Method 3: Very Small Batches

If you must download multiple videos:

```bash
# Edit manifest_urls.json to have only 3-5 videos
python download_lectures.py
```

**Then:**
- Wait 5-10 minutes
- Edit manifest_urls.json with next batch
- Repeat

---

### Method 4: Download at Off-Peak Hours

Server load varies by time:
- ✅ **Best:** Late night (11 PM - 6 AM)
- ✅ **Good:** Early morning (6 AM - 9 AM)
- ⚠️ **Avoid:** Peak hours (9 AM - 5 PM)

---

## 🔍 Understanding the Error

When you see:
```
❌ Failed to download: Lecture_09.mp4
   Error: HTTP error 429
   Server returned 429 Too Many Requests
```

**This means:**
- Server is rate-limiting you
- You've made too many requests too quickly
- You need to slow down

**The script will:**
1. Detect the 429 error
2. Wait 30 seconds
3. Retry automatically (up to 2 times)
4. If still failing, log it for manual retry later

---

## 📊 Configuration Options

Edit `download_lectures.py` to adjust rate limiting:

```python
# Around line 24-26
DELAY_BETWEEN_DOWNLOADS = 3  # Increase to 5 or 10 seconds
MAX_RETRIES_ON_429 = 2       # Increase retry attempts
RETRY_DELAY_429 = 30         # Increase wait time (e.g., 60 seconds)
```

**Recommended settings for problematic servers:**
```python
DELAY_BETWEEN_DOWNLOADS = 10  # 10 seconds between each
MAX_RETRIES_ON_429 = 3        # 3 retry attempts
RETRY_DELAY_429 = 60          # Wait 1 minute on 429
```

---

## 🛠️ Troubleshooting 429 Errors

### Still Getting 429 Errors?

**Try these in order:**

1. **Wait Longer Between Downloads**
   - Increase `DELAY_BETWEEN_DOWNLOADS` to 10 seconds

2. **Use Absolute Sequential Mode**
   - Never use `--parallel` flag
   - Download one subject at a time

3. **Smaller Batches**
   - Only 3-5 videos in manifest_urls.json at once

4. **Different Time of Day**
   - Try late night or early morning

5. **Contact Your Institution**
   - Your IT may have additional rate limits
   - They might whitelist your account

---

## 📝 Example Workflow

### Recommended Workflow to Avoid 429:

```bash
# Step 1: Test with one video first
cd scripts
python simple_download.py "URL_OF_ONE_VIDEO" "test.mp4"

# Step 2: If successful, configure small batch
# Edit manifest_urls.json - add only 5 videos
nano manifest_urls.json

# Step 3: Download with sequential mode
python download_lectures.py
# Select subject and wait

# Step 4: If 429 occurs
# Script auto-waits 30 seconds and retries

# Step 5: For remaining videos
# Wait 10-15 minutes
# Edit manifest_urls.json with next 5 videos
# Repeat
```

---

## 🎯 Key Takeaways

1. ✅ **Sequential mode** is most reliable
2. ✅ **Small batches** (5-10 videos) work best
3. ✅ **Delays are automatic** (3 seconds between downloads)
4. ✅ **Auto-retry** handles temporary 429 errors
5. ⚠️ **Avoid parallel downloads** for SharePoint/Teams
6. ⏰ **Download at off-peak hours** if possible
7. 🧪 **Test with one video** using `simple_download.py`

---

## 🆘 If Nothing Works

If you still can't download despite all attempts:

1. **Check URL expiry** - Get fresh URLs
2. **Try different network** - Use different WiFi/location
3. **Contact IT support** - Your institution may block bulk downloads
4. **Use browser download** - As a last resort, download via browser
5. **VPN/Proxy** - Server might be geo-restricted

---

**Remember:** The 429 error is the **server protecting itself** from too many requests. Respect the rate limits and download patiently. 🙏
