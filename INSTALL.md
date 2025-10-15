# 🚀 Installation Guide - GenVR Batch Processor

## For Windows Users

### Step 1: Install Python

1. **Download Python:**
   - Go to https://www.python.org/downloads/
   - Click the big yellow "Download Python" button
   - Download will start automatically

2. **Install Python:**
   - Run the downloaded installer
   - ⚠️ **IMPORTANT:** Check the box "Add Python to PATH"
   - Click "Install Now"
   - Wait for installation to complete
   - Click "Close"

3. **Verify Installation:**
   - Press `Windows Key + R`
   - Type `cmd` and press Enter
   - Type `python --version`
   - You should see: `Python 3.x.x`

### Step 2: Download GenVR Batch Processor

**Option A: Download ZIP**
1. Click the green "Code" button on GitHub
2. Click "Download ZIP"
3. Extract the ZIP file to a folder (e.g., `C:\GenVR`)

**Option B: Git Clone**
```bash
git clone https://github.com/yourusername/GenVR-Batch-Processor.git
cd GenVR-Batch-Processor
```

### Step 3: Run the Application

1. Navigate to the extracted folder
2. **Double-click `run_qt.bat`**
3. First time: Dependencies will install automatically (takes 1-2 minutes)
4. Application will launch!

### Step 4: Configure API

1. Enter your **User ID** (UID)
2. Enter your **API Key** (Bearer token)
3. Start using the app!

---

## For Mac/Linux Users

### Step 1: Install Python

**Mac:**
```bash
# Check if Python is installed
python3 --version

# If not installed, use Homebrew
brew install python3
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip
```

**Linux (CentOS/RHEL):**
```bash
sudo yum install python3 python3-pip
```

### Step 2: Clone Repository

```bash
git clone https://github.com/yourusername/GenVR-Batch-Processor.git
cd GenVR-Batch-Processor
```

### Step 3: Install Dependencies

```bash
pip3 install -r requirements.txt
```

### Step 4: Run Application

**Using shell script:**
```bash
chmod +x run_qt.sh
./run_qt.sh
```

**Or run directly:**
```bash
python3 main_qt.py
```

---

## 🎯 First Time Setup

### Get Your API Credentials

1. Visit [GenVR Research](https://genvrresearch.com)
2. Sign up or log in
3. Get your:
   - **UID** (User ID)
   - **API Key** (Bearer token)

### Enter Credentials in App

1. Launch the application
2. In the top-right corner:
   - Enter your **User ID**
   - Enter your **API Key**
3. Credentials are ready!

---

## ✅ Verification

### Test the Installation

1. **Launch app** (run_qt.bat or run_qt.sh)
2. **Select Category:** imagegen
3. **Select Model:** google_imagen4
4. **Enter a prompt:** "a beautiful sunset"
5. **Click:** ▶️ Generate Single
6. **Check Results tab** - You should see the API response!

If you see results, everything is working! 🎉

---

## 🆘 Common Issues

### "Python not found" (Windows)

**Problem:** Python not in PATH

**Solution:**
1. Reinstall Python
2. Check "Add Python to PATH"
3. OR manually add to PATH:
   - Search "Environment Variables" in Windows
   - Edit PATH
   - Add: `C:\Users\YourName\AppData\Local\Programs\Python\Python3xx`

### "pip not found"

**Solution:**
```bash
python -m ensurepip --upgrade
python -m pip install --upgrade pip
```

### "ModuleNotFoundError: No module named 'PySide6'"

**Solution:**
```bash
pip install PySide6
```

### "Permission Denied" (Unix)

**Solution:**
```bash
chmod +x run_qt.sh
# Then run again
./run_qt.sh
```

### Application Won't Start

**Solution:**
```bash
# Run directly to see errors
python main_qt.py
```

---

## 🔄 Updating

To get the latest version:

```bash
cd GenVR-Batch-Processor
git pull
pip install -r requirements.txt --upgrade
```

---

## 💡 Tips

- **Use Qt version** for the best experience
- **Start with 3 concurrent requests** - increase if your API allows
- **Generate from folder** works best with organized file structures
- **Stop button** - Cancel batch processing anytime
- **Export results** - Save JSON for later analysis

---

## 📚 Additional Documentation

- [Quick Start Guide](QUICKSTART.md) - Fast setup and usage
- [Categories Guide](CATEGORIES_GUIDE.md) - All available model categories
- [PyQt Version Details](PYQT_VERSION.md) - Qt-specific features

---

## 🎉 You're Ready!

Now you can:
- ✅ Generate images with 100+ image models
- ✅ Create videos with 50+ video models
- ✅ Process images with 100+ utility models
- ✅ Batch process hundreds of requests
- ✅ Download all outputs automatically

Happy generating! 🚀

