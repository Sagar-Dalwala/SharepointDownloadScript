# 🚀 Quick Start Guide

## 1️⃣ Install Prerequisites

### Install FFmpeg
```bash
# Windows (with Chocolatey)
choco install ffmpeg

# macOS
brew install ffmpeg

# Linux (Ubuntu/Debian)
sudo apt install ffmpeg
```

Verify:
```bash
ffmpeg -version
```

### Install Python Packages
```bash
cd scripts
pip install -r requirements.txt
```

## 2️⃣ Setup Configuration

```bash
cd scripts
cp manifest_urls.example.json manifest_urls.json
```

Edit `manifest_urls.json` and add your videomanifest URLs.

## 3️⃣ Download Videos

### Basic (Sequential)
```bash
python download_lectures.py
```

### Faster (Parallel - Recommended)
```bash
python download_lectures.py --parallel 3
```

### Retry Failed Downloads
```bash
python download_lectures.py --retry --parallel 3
```

## 📝 Getting videomanifest URLs

1. Open Teams → Class channel → Files
2. Right-click recording → "Open in SharePoint"
3. Click "Download" (don't actually download)
4. Open DevTools (F12) → Network tab
5. Look for `videomanifest` request
6. Copy the full URL

## ⚠️ Important Notes

- **URLs expire in 6-24 hours** - download in batches
- **Batch size**: 10-20 videos per session recommended
- **Parallel downloads**: Use 3-5 for optimal speed
- **Storage**: ~1-2 GB per hour of video

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ffmpeg not found` | Install ffmpeg and add to PATH |
| `403 Forbidden` | URLs expired - fetch fresh ones |
| Slow downloads | Reduce `--parallel` to 1 or 2 |
| Validation failed | Script auto-retries with re-encoding |

## 📁 Output Structure

```
IITP/
├── AML/
│   └── Lectures/
│       ├── Lecture_01_Introduction.mp4
│       ├── Lecture_02_Linear_Regression.mp4
│       └── ...
├── DAA/
│   └── Lectures/
│       └── ...
└── scripts/
    ├── download_lectures.py
    ├── manifest_urls.json
    └── failed_downloads.json (if any fail)
```

## 🎉 That's It!

The script will:
- ✅ Auto-create folders
- ✅ Download with progress
- ✅ Validate video duration
- ✅ Send desktop notifications
- ✅ Handle errors gracefully
- ✅ Log failures for retry

**Need help?** Check the full [README.md](../README.md)
