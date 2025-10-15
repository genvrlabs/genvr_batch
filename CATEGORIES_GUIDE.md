# GenVR API Categories Guide

Complete guide to all 308 available models across 12 categories.

## Overview

The GenVR API provides access to 308 AI models across various categories. The application automatically filters to show only **actually available models** by cross-referencing `/api/models` with `/api/get-models`.

---

## 1. Image Generation (42 models)

**Category**: `imagegen`

High-quality AI image generation from text prompts.

### Popular Models:
- `flux1_1_pro_ultra` - Flux 1.1 Pro Ultra (highest quality)
- `openai_dalle_3` - OpenAI DALL-E 3
- `google_imagen4` - Google Imagen 4
- `google_imagen4_ultra` - Google Imagen 4 Ultra
- `stable_diffusion_3_5` - Stable Diffusion 3.5
- `ideogram_v3` - Ideogram V3
- `recraft_v3` - Recraft V3
- `flux_dev` - Flux Dev
- `bytedance_seedream4` - ByteDance SeeDream 4
- `minimax-image-o1` - MiniMax Image-o1

### Common Parameters:
- `prompt` (required) - Text description
- `aspect_ratio` - Image dimensions (1:1, 16:9, 9:16, etc.)
- `seed` - For reproducible results

---

## 2. Video Generation (81 models)

**Category**: `videogen`

Text-to-video and image-to-video generation.

### Popular Models:
- `sora2_pro_t2v` - OpenAI Sora 2 Pro (text-to-video)
- `google_veo3_t2v` - Google Veo 3 (text-to-video)
- `google_veo3_i2v` - Google Veo 3 (image-to-video)
- `runway_gen4_turbo` - Runway Gen4 Turbo
- `luma_ray2_t2v` - Luma Ray2 (text-to-video)
- `luma_ray2_i2v` - Luma Ray2 (image-to-video)
- `kling2_5_t2v` - Kling 2.5 (text-to-video)
- `kling2_5_i2v` - Kling 2.5 (image-to-video)
- `minimax_video_o1` - MiniMax Video-o1
- `hunyuan_video` - Hunyuan Video
- `pika2_2_t2v` - Pika 2.2

### Common Parameters:
- `prompt` (required) - Video description
- `image_url` - First frame for i2v models
- `duration` - Video length (5s, 10s, etc.)
- `ratio` - Aspect ratio

---

## 3. Image Editing (34 models)

**Category**: `imgedit`

Advanced image manipulation and enhancement tools.

### Available Tools:
- `background_change` - Change image background
- `background_replace` - Replace background
- `object_removal` - Remove unwanted objects
- `face_enhance` - Enhance face quality
- `face_realism` - Improve face realism
- `expression_change` - Change facial expression
- `hair_change` - Modify hairstyle
- `deaging` - Make faces younger
- `cartoonify` - Convert to cartoon style
- `stylize_flux` - Apply Flux stylization
- `stylize_sdxl` - Apply SDXL stylization
- `color_correction` - Fix colors
- `filters` - Apply artistic filters
- `restore_image` - Restore old/damaged images
- `text_removal` - Remove text from images
- `professional_shot` - Professional photography look
- `face_to_sticker_sdxl` - Convert face to sticker
- `interior_remodel` - Remodel interior spaces
- `product_shot` - Product photography
- `eraser` - Precision object removal

### Common Parameters:
- `image_url` (required) - Input image
- `prompt` - Desired changes
- `strength` - Effect intensity

---

## 4. Video Utilities (42 models)

**Category**: `vidutils`

Video processing, enhancement, and editing tools.

### Available Tools:

**Lipsync & Animation:**
- `hummingbird_lipsync` - High-quality lipsync
- `kling_lip_sync` - Kling lipsync
- `multitalk_lipsync_single` - Single speaker lipsync
- `multitalk_lipsync_multi` - Multi-speaker lipsync
- `sync_lipsync2` - Sync Lipsync 2
- `kling_avatar` - Kling avatar animation
- `stable_avatar` - Stable avatar

**Enhancement:**
- `videoupscale` - Upscale video resolution
- `topaz_upscale` - Topaz AI upscale
- `runway_upscale` - Runway upscale
- `bria_upscale` - Bria upscale
- `videofacerestore` - Restore faces in video

**Background & Effects:**
- `videobgremove` - Remove video background
- `videobgremove_bria` - Bria background removal
- `minimax_remover` - MiniMax background remover

**Audio:**
- `mmaudio` - Add audio to video
- `hunyuan_foley_add_audio` - Add foley sound effects
- `mirelo_add_audio` - Mirelo audio addition
- `thinksound` - AI sound generation

**Other:**
- `runway_act2` - Runway Act2
- `luma_ray2_modify_video` - Modify existing videos
- `heygen_video_translate` - Translate video
- `sora2_watermark_remover` - Remove watermarks

---

## 5. Video Templates (39 models)

**Category**: `videogen_templates`

Pre-built video effects and templates.

### Available Templates:
- `morphlab` - Morphing transitions
- `live_memory` - Animate old photos
- `christmas` - Christmas effects
- `zombie_mode` - Zombie transformation
- `muscle_surge` - Muscle enhancement
- `hulk` - Hulk transformation
- `captain_america` - Captain America effect
- `kissing` / `hugging` - Romantic effects
- `dreamy_wedding` - Wedding effects
- `shake_it_dance` - Dance animation
- `eye_zoom_challenge` - Eye zoom effect
- `balloon_flyaway` - Balloon effect
- `french_kiss` / `kiss_me_ai` - Kiss effects
- `fashion_stride` - Fashion walk
- `star_carpet` - Red carpet effect

### Common Parameters:
- `image_url` (required) - Input photo
- Template-specific settings vary

---

## 6. Image Utilities (27 models)

**Category**: `imgutils`

Advanced image processing and manipulation.

### Available Tools:
- `topaz_upscale` - Topaz AI upscale
- `recraft_crisp_upscale` - Crisp upscaling
- `recraft_creative_upscale` - Creative upscaling
- `ideogram_upscale` - Ideogram upscale
- `inpainting` - Fill masked areas
- `variations` - Create image variations
- `flux_kontext_dev` - Flux context-aware editing
- `flux_kontext_pro` - Flux Pro context editing
- `gemini_flash2_imgedit` - Gemini Flash image edit
- `step1x_edit` - Step1x editing
- `gpt_image1_edit` - GPT image editing
- `bytedance_bagel` - ByteDance Bagel
- `bytedance_seededit3` - SeeDEdit 3
- `bytedance_seededit4` - SeeDEdit 4
- `qwen_image_edit` - Qwen image editing
- `luma_reframe_image` - Reframe/resize images
- `frame_extractor` - Extract video frames
- `ideogram_character` - Character generation

---

## 7. Audio Generation (13 models)

**Category**: `audiogen`

AI-powered audio, music, and voice generation.

### Available Models:
- `elevenlabs_sound_effects` - ElevenLabs sound FX
- `elevenlabs_sound_effects2` - ElevenLabs SFX v2
- `google_lyria2` - Google Lyria 2
- `minimax_music1_5` - MiniMax Music 1.5
- `sonauto_text2music` - Sonauto music generation
- `ace_step_text2music` - ACE STEP music
- `chatterbox_tts` - Chatterbox TTS
- `chatterbox_multilingual` - Multilingual TTS
- `microsoft_vibevoice` - Microsoft VibeVoice
- `cartesia_sonic2` - Cartesia Sonic 2
- `minimax_speech_02_hd` - MiniMax Speech HD
- `dia` - DIA audio generation

### Common Parameters:
- `prompt` - Audio description
- `duration` - Audio length
- `voice` - Voice selection (for TTS)

---

## 8. 3D Generation (8 models)

**Category**: `3dgen`

Generate 3D models from images or text.

### Available Models:
- `trellis` - Trellis 3D
- `hunyuan2_3d_2_1` - Hunyuan 3D 2.1
- `hunyuan2_3d` - Hunyuan 3D 2.0
- `hunyuan_3d_2mv` - Hunyuan 3D multi-view
- `tripo3d_2_5` - Tripo 3D 2.5
- `meshy3d_v6` - Meshy 3D V6
- `hyper3d_rodin_v2` - Hyper3D Rodin V2
- `panorama` - 360° panorama generation

### Common Parameters:
- `image_url` - Input image
- `prompt` - 3D model description
- `texture_quality` - Texture resolution

---

## 9. Image Transfer (8 models)

**Category**: `imgutils_transfer`

Transfer faces, styles, garments, and materials.

### Available Models:
- `face` - Face swap/transfer
- `easel_face_swap` - Easel face swap
- `garment` - Garment transfer
- `fashn_tryon` - Fashion virtual try-on
- `easel_fashion_photoshoot` - Fashion photoshoot
- `easel_virtual_tryon` - Virtual try-on
- `material` - Material transfer
- `style` - Style transfer

### Common Parameters:
- `source_image` - Source image
- `target_image` - Target image
- `blend_strength` - Blending intensity

---

## 10. Image Control (6 models)

**Category**: `imgutils_control`

ControlNet preprocessors for guided generation.

### Available Models:
- `canny` - Canny edge detection
- `pose` - Pose detection
- `depth` - Depth map generation
- `scribble2img` - Scribble to image
- `hed` - HED edge detection
- `controlnet_preprocessors` - Various preprocessors

### Use Case:
Generate control maps for guided image generation with precise control over composition, pose, edges, etc.

---

## 11. Basic Utilities (5 models)

**Category**: `basicutils`

Utility tools for composition and merging.

### Available Models:
- `arrayindexer` - Index and select from arrays
- `arraybuilder` - Build arrays of outputs
- `imagecompositor` - Composite multiple images
- `audio_video_merge` - Merge audio with video
- `video_video_merge` - Merge multiple videos

---

## 12. Text Generation (3 models)

**Category**: `textgen`

AI text generation and workflow design.

### Available Models:
- `gpt_4o_mini` - GPT-4o Mini
- `openai_gpt5` - OpenAI GPT-5
- `workflow_designer` - Workflow automation designer

---

## Using in the Application

1. **Launch the app** and enter your UID + API Key
2. **Select a category** from the dropdown
3. **Choose a model** from the list
4. **Fill parameters** - The form auto-generates based on the schema
5. **Generate** single or batch process

## Batch Processing Tips

- Use **JSON Lines** format (one object per line)
- Load from **CSV or JSON** files
- Set **concurrent requests** (1-10)
- Monitor progress in real-time

## Example Workflows

### Image Generation Workflow
```
Category: imagegen
Model: flux1_1_pro_ultra
Parameters: {prompt: "...", aspect_ratio: "16:9"}
```

### Video Creation Workflow
```
1. Generate image → imagegen/google_imagen4
2. Animate image → videogen/luma_ray2_i2v
3. Add lipsync → vidutils/hummingbird_lipsync
4. Add audio → vidutils/mmaudio
```

### 3D Model Workflow
```
1. Generate image → imagegen/flux1_1_pro_ultra
2. Create 3D model → 3dgen/hunyuan2_3d_2_1
```

---

## Resources

- **API Documentation**: https://api.genvrresearch.com
- **Model Schemas**: `https://api.genvrresearch.com/api/schema/{category}/{subcategory}`
- **Available Models**: `https://api.genvrresearch.com/api/get-models`

---

*Last Updated: October 2025*
*Total Models: 308*

