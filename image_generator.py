import os
import requests
import time
import uuid
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("automarketer")

class ImageGeneratorError(Exception):
    """Custom exception for Hugging Face Inference API failures."""
    pass

def generate_fallback_svg(filepath: str, prompt: str):
    """Generates a beautiful, responsive vector graphic (SVG) mockup representing the campaign asset."""
    # Truncate prompt for display in the mockup
    display_prompt = prompt if len(prompt) < 70 else prompt[:67] + "..."
    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="100%" height="100%">
        <defs>
            <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#8b5cf6;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#06b6d4;stop-opacity:1" />
            </linearGradient>
            <filter id="glow">
                <feGaussianBlur stdDeviation="15" result="coloredBlur"/>
                <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                </feMerge>
            </filter>
        </defs>
        
        <!-- Background -->
        <rect width="100%" height="100%" fill="#0c1122"/>
        
        <!-- Glow design shapes -->
        <circle cx="200" cy="150" r="140" fill="url(#grad)" opacity="0.15" filter="url(#glow)"/>
        <circle cx="650" cy="450" r="180" fill="url(#grad)" opacity="0.12" filter="url(#glow)"/>
        
        <!-- Grid pattern overlay -->
        <g stroke="rgba(255,255,255,0.02)" stroke-width="1">
            <line x1="0" y1="100" x2="800" y2="100"/>
            <line x1="0" y1="200" x2="800" y2="200"/>
            <line x1="0" y1="300" x2="800" y2="300"/>
            <line x1="0" y1="400" x2="800" y2="400"/>
            <line x1="0" y1="500" x2="800" y2="500"/>
            <line x1="100" y1="0" x2="100" y2="600"/>
            <line x1="200" y1="0" x2="200" y2="600"/>
            <line x1="300" y1="0" x2="300" y2="600"/>
            <line x1="400" y1="0" x2="400" y2="600"/>
            <line x1="500" y1="0" x2="500" y2="600"/>
            <line x1="600" y1="0" x2="600" y2="600"/>
            <line x1="700" y1="0" x2="700" y2="600"/>
        </g>
        
        <!-- Frame -->
        <rect x="25" y="25" width="750" height="550" rx="16" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="2"/>
        
        <!-- Interactive App Display mockup representation -->
        <rect x="150" y="150" width="500" height="300" rx="12" fill="rgba(13,18,35,0.8)" stroke="rgba(255,255,255,0.08)" stroke-width="1.5" filter="drop-shadow(0 20px 40px rgba(0,0,0,0.5))"/>
        
        <!-- App Header mockup -->
        <line x1="150" y1="190" x2="650" y2="190" stroke="rgba(255,255,255,0.08)" stroke-width="1"/>
        <circle cx="175" cy="170" r="5" fill="#ef4444"/>
        <circle cx="190" cy="170" r="5" fill="#f59e0b"/>
        <circle cx="205" cy="170" r="5" fill="#10b981"/>
        
        <!-- Dynamic visuals mockup inside representation -->
        <rect x="180" y="220" width="120" height="180" rx="8" fill="rgba(255,255,255,0.02)" stroke="rgba(255,255,255,0.04)" stroke-width="1"/>
        <rect x="320" y="220" width="300" height="15" rx="4" fill="url(#grad)" opacity="0.8"/>
        <rect x="320" y="250" width="220" height="10" rx="3" fill="rgba(255,255,255,0.3)"/>
        <rect x="320" y="275" width="260" height="10" rx="3" fill="rgba(255,255,255,0.3)"/>
        
        <!-- Chart mockup representation -->
        <path d="M 320 370 L 380 330 L 440 350 L 500 310 L 560 340 L 620 290" fill="none" stroke="#06b6d4" stroke-width="3" filter="drop-shadow(0 4px 6px rgba(6,182,212,0.4))"/>
        <circle cx="620" cy="290" r="4" fill="#06b6d4"/>
        
        <!-- Emojis & branding -->
        <text x="400" y="100" font-family="'Outfit', sans-serif" font-size="32" font-weight="800" fill="#ffffff" text-anchor="middle" letter-spacing="-0.5">AutoMarketer <tspan fill="url(#grad)">AI</tspan></text>
        <text x="400" y="125" font-family="'Inter', sans-serif" font-size="13" fill="#94a3b8" text-anchor="middle" letter-spacing="1.5" opacity="0.6">VISUAL CONCEPT BRAND ASSET</text>
        
        <!-- Footer Prompt block -->
        <rect x="80" y="490" width="640" height="60" rx="10" fill="rgba(0,0,0,0.5)" stroke="rgba(255,255,255,0.04)" stroke-width="1"/>
        <text x="400" y="515" font-family="'Inter', sans-serif" font-size="11" fill="#a78bfa" text-anchor="middle" font-weight="bold" letter-spacing="1">HF PROMPT CONCEPT</text>
        <text x="400" y="535" font-family="monospace" font-size="11" fill="#94a3b8" text-anchor="middle" font-style="italic">"{display_prompt}"</text>
        
        <!-- Mode Badge -->
        <rect x="25" y="25" width="130" height="26" rx="8" fill="rgba(16,185,129,0.12)" stroke="rgba(16,185,129,0.3)" stroke-width="1"/>
        <text x="90" y="42" font-family="'Inter', sans-serif" font-size="10" fill="#10b981" text-anchor="middle" font-weight="bold">OFFLINE PREVIEW</text>
    </svg>"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(svg_content)

def extract_keywords(text: str) -> str:
    """Extracts 2-3 clean, relevant keywords from the text for stock image search."""
    stop_words = {
        'a', 'an', 'the', 'in', 'on', 'at', 'for', 'with', 'by', 'from', 'to', 'of', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
        'modern', 'futuristic', 'cinematic', 'glowing', 'neon', 'lights', 'graphic', 'graphic,', 'design', 'branding', 'creative',
        'concept', 'vibrant', 'premium', 'high-quality', 'high', 'quality', 'style', 'digital', 'marketing', 'illustration',
        'banner', 'visual', 'artwork', 'abstract', 'art', 'background', 'featuring', 'featuring,', 'layout', 'minimalist',
        'professional', 'sleek', 'dark', 'light', 'beautiful', 'stunning', 'artistic', 'clean', 'simple', 'bold',
        'lit', 'cityscape', 'dusk', 'cozy', 'living', 'scene',
        # Website title stop words
        'watch', 'online', 'free', 'home', 'website', 'page', 'official', 'site', 'india', 'welcome',
        'login', 'signin', 'signup', 'portal', 'dashboard', 'app', 'web', 'com', 'org', 'net',
        '–', '-', '|', '—'
    }
    cleaned_text = text.lower().replace('–', ' ').replace('-', ' ').replace('|', ' ').replace('—', ' ').replace(',', ' ').replace('.', ' ').replace('_', ' ')
    words = []
    for word in cleaned_text.split():
        clean_word = ''.join(c for c in word if c.isalpha())
        if len(clean_word) > 2 and clean_word not in stop_words:
            words.append(clean_word)
            
    unique_words = []
    for w in words:
        if w not in unique_words:
            unique_words.append(w)
            
    if not unique_words:
        return "marketing"
        
    return ",".join(unique_words[:3])

def generate_and_save_image(prompt: str, images_dir: str = "images", page_title: str = None, stock_keywords: str = None) -> str:
    """
    Attempts to generate a campaign image in a 4-tier fallback model:
    1. Hugging Face Inference API (if key is set and reachable)
    2. LoremFlickr (semantically related images from Flickr based on title/prompt/stock keywords)
    3. Picsum Photos (random high-quality photo based on prompt seed)
    4. Custom SVG mockup (vector graphic fallback)
    """
    os.makedirs(images_dir, exist_ok=True)
    
    hf_api_key = os.getenv("HF_API_KEY")
    has_hf_key = hf_api_key and hf_api_key != "your_hugging_face_api_token_here" and not hf_api_key.startswith("your_")
    
    if has_hf_key:
        model_id = os.getenv("HF_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell")
        api_url = f"https://api-inference.huggingface.co/models/{model_id}"
        headers = {
            "Authorization": f"Bearer {hf_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "inputs": prompt
        }
        
        filename = f"campaign_{uuid.uuid4().hex}.png"
        filepath = os.path.join(images_dir, filename)
        
        max_retries = 3
        retry_delay = 5
        
        logger.info(f"Sending image generation request to HF Model: {model_id}")
        
        for attempt in range(max_retries):
            try:
                response = requests.post(api_url, headers=headers, json=payload, timeout=25)
                
                # Hugging Face returns a loading status with 503 sometimes:
                if response.status_code == 503:
                    error_data = response.json()
                    est_time = error_data.get("estimated_time", retry_delay)
                    logger.warning(f"Model {model_id} is loading. Waiting {est_time}s (Attempt {attempt+1}/{max_retries})...")
                    time.sleep(min(est_time, 15))
                    continue
                    
                if response.status_code == 200:
                    content_type = response.headers.get("Content-Type", "")
                    if "image" in content_type or len(response.content) >= 1000:
                        with open(filepath, "wb") as f:
                            f.write(response.content)
                        logger.info(f"Successfully generated and saved image: {filepath}")
                        return f"/images/{filename}"
                
                # If we get here, it failed. Raise error to trigger fallback.
                raise Exception(f"HF returned HTTP {response.status_code}")
                
            except Exception as e:
                logger.warning(f"Attempt {attempt+1} calling Hugging Face failed: {str(e)}")
                if attempt == max_retries - 1:
                    logger.warning("Hugging Face attempts exhausted. Moving to fallbacks.")
    else:
        logger.warning("Hugging Face API key is missing or placeholder. Skipping to semantic fallbacks.")

    # FALLBACK 1: LoremFlickr (Semantic related images)
    try:
        # Use LLM-generated keywords if provided, otherwise extract from page_title, otherwise prompt
        if stock_keywords:
            keywords = stock_keywords
        else:
            text_to_parse = page_title if page_title else prompt
            keywords = extract_keywords(text_to_parse)
        logger.info(f"Attempting LoremFlickr semantic fallback with keywords: {keywords}")
        flickr_url = f"https://loremflickr.com/800/600/{keywords}"
        response = requests.get(flickr_url, timeout=20, allow_redirects=True)
        if response.status_code == 200 and "image" in response.headers.get("Content-Type", ""):
            filename = f"campaign_{uuid.uuid4().hex}.jpg"
            filepath = os.path.join(images_dir, filename)
            with open(filepath, "wb") as f:
                f.write(response.content)
            logger.info(f"Successfully retrieved and saved semantic image from LoremFlickr for keywords: {keywords}")
            return f"/images/{filename}"
        else:
            raise Exception(f"LoremFlickr returned HTTP {response.status_code} or non-image content")
    except Exception as fe:
        logger.warning(f"LoremFlickr fallback failed: {fe}. Attempting Picsum Photos fallback...")

    # FALLBACK 2: Picsum Photos (Random high-quality image with seed)
    try:
        import hashlib
        seed = hashlib.md5(prompt.encode('utf-8')).hexdigest()
        picsum_url = f"https://picsum.photos/seed/{seed}/800/600"
        response = requests.get(picsum_url, timeout=20)
        if response.status_code == 200:
            filename = f"campaign_{uuid.uuid4().hex}.jpg"
            filepath = os.path.join(images_dir, filename)
            with open(filepath, "wb") as f:
                f.write(response.content)
            logger.info("Successfully generated and saved fallback image from Picsum Photos.")
            return f"/images/{filename}"
        else:
            raise Exception(f"Picsum returned HTTP {response.status_code}")
    except Exception as pe:
        logger.error(f"Picsum fallback failed: {str(pe)}. Generating fallback SVG mockup.")

    # FALLBACK 3: SVG Mockup
    filename = f"campaign_{uuid.uuid4().hex}.svg"
    filepath = os.path.join(images_dir, filename)
    generate_fallback_svg(filepath, prompt)
    return f"/images/{filename}"

