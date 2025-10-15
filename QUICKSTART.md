# Quick Start Guide

## 🚀 Getting Started in 3 Steps

### 1. Install Dependencies

**Windows:**
```bash
run.bat
```

**Mac/Linux:**
```bash
chmod +x run.sh
./run.sh
```

Or manually:
```bash
pip install -r requirements.txt
python main.py
```

### 2. Configure API Credentials

1. Launch the application
2. Enter your credentials in the top-right "API Configuration" section:
   - **UID**: Your GenVR user ID
   - **API Key**: Your GenVR Bearer token
3. These credentials will be used for all requests

**Note:** Get your credentials from [GenVR Research](https://api.genvrresearch.com)

### 3. Start Creating!

#### Option A: Single Request
1. Select a **Category** (e.g., "imagegen")
2. Choose a **Model** (e.g., "Google Imagen 4")
3. Fill in the parameters in the **"Single Request"** tab
4. Click **"Generate (Single)"**
5. View results in the **"Results"** tab

#### Option B: Batch Processing
1. Select a **Category** and **Model**
2. Go to the **"Batch Processing"** tab
3. Load example data:
   - Click **"Load from JSON"** → select `example_batch.json`
   - OR click **"Load from CSV"** → select `example_batch.csv`
4. Click **"Start Batch Processing"**
5. Watch the progress bar and view results in real-time

---

## 📋 Example Use Cases

### Image Generation Batch
```json
{"prompt": "mountain sunset", "aspect_ratio": "16:9"}
{"prompt": "city skyline", "aspect_ratio": "1:1"}
```

### Video Generation
```json
{"prompt": "waves crashing", "image_url": "https://example.com/img.jpg", "duration": 5}
```

### Multiple Categories
You can switch between different categories (imagegen, videogen, audiogen) and process different types of content in the same session!

---

## 💡 Tips

- **Required fields** are marked with an asterisk (*)
- Use the **description** text below each field for guidance
- Export your results anytime from the Results tab
- Adjust **Concurrent Requests** for faster batch processing
- The app remembers your last selected model

---

## 🆘 Need Help?

**Can't see models?**
- Check your internet connection
- The app loads 300+ models from the API on startup

**API errors?**
- Verify both your UID and API key are correct
- Check if you have sufficient credits
- Some models may have specific requirements
- Watch the status bar for detailed progress updates

**Batch processing stuck?**
- Click "Stop" to cancel current batch
- Check the Results tab for any error messages
- Reduce concurrent requests if experiencing timeouts

---

## 🎨 Available Categories (308 Models)

- **imagegen** (42) - Image generation (Flux 1.1 Pro Ultra, DALL-E 3, Imagen 4, Stable Diffusion 3.5, etc.)
- **videogen** (81) - Video generation (Runway Gen4, Luma Ray2, Kling 2.5, Google Veo3, Sora2, etc.)
- **imgedit** (34) - Image editing (background change, face enhance, style transfer, filters, etc.)
- **vidutils** (42) - Video utilities (lipsync, upscale, background removal, audio addition, etc.)
- **videogen_templates** (39) - Pre-made video templates and effects
- **imgutils** (27) - Image utilities (upscale, inpainting, variations, reframing, etc.)
- **audiogen** (13) - Audio generation (ElevenLabs, Google Lyria 2, MiniMax, etc.)
- **3dgen** (8) - 3D model generation (Trellis, Hunyuan 3D 2.1, Meshy, Tripo, etc.)
- **imgutils_transfer** (8) - Face/garment/material/style transfer
- **imgutils_control** (6) - ControlNet preprocessors (canny, pose, depth, scribble, etc.)
- **basicutils** (5) - Utility tools (array indexer, image compositor, video merge, etc.)
- **textgen** (3) - Text generation (GPT-4o Mini, GPT-5, Workflow Designer)

---

Happy creating! 🎉

