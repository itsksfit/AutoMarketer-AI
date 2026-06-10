import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("automarketer")

class LLMError(Exception):
    """Custom exception for LLM related failures."""
    pass

def generate_marketing_caption(page_content: str) -> str:
    """
    Generates a professional 2-sentence marketing caption based on scraped content using Groq.
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise LLMError("Groq API key is missing. Please set GROQ_API_KEY in your environment.")
        
    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    api_url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = (
        "You are an expert copywriter and digital marketer. Based on the following scraped website content, "
        "write a highly professional, engaging, and persuasive marketing caption for a campaign. "
        "The caption MUST be EXACTLY two sentences long. Do not include hashtags, markdown formatting, "
        "or any introductory text. Just return the caption itself.\n\n"
        f"Website Content:\n{page_content}"
    )
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 150
    }
    
    logger.info("Generating marketing caption from content using Groq...")
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=20)
        if response.status_code != 200:
            raise LLMError(f"Groq API returned HTTP {response.status_code}: {response.text}")
            
        data = response.json()
        caption = data["choices"][0]["message"]["content"].strip()
        if not caption:
            raise LLMError("Groq returned an empty response.")
            
        # Clean up formatting
        caption = caption.replace('"', '').replace('\n', ' ')
        logger.info("Successfully generated marketing caption using Groq.")
        return caption
    except Exception as e:
        logger.error(f"Groq caption generation error: {str(e)}")
        raise LLMError(f"Groq API failed to generate caption: {str(e)}")

def generate_image_prompt(caption: str) -> str:
    """
    Generates a detailed text-to-image prompt from the marketing caption using Groq.
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise LLMError("Groq API key is missing. Please set GROQ_API_KEY in your environment.")
        
    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    api_url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = (
        "You are an expert art director and AI prompt designer. Based on the following marketing caption, "
        "write a detailed, high-quality, and descriptive image-generation prompt for a text-to-image model "
        "(like Stable Diffusion or FLUX). "
        "The prompt MUST be directly and literally related to the core subject, product, or service described in the caption. "
        "For example, if the caption is about software, content creation, or business, show a clean modern office workspace, laptop, or software dashboard. "
        "If it is about movies, entertainment, or streaming, show a cozy living room home theater with a television. "
        "Avoid generic/abstract visual templates like futuristic cityscapes, abstract neon grids, or code vortexes unless the product is specifically about urban planning or networking hardware. "
        "Focus on realistic composition, professional photography style, and clear subject matter. "
        "Keep the prompt under 70 words. Do not include introductory text or quotes. "
        "Just output the prompt text itself.\n\n"
        f"Marketing Caption: {caption}"
    )
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 150
    }
    
    logger.info("Generating image prompt using Groq...")
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=20)
        if response.status_code != 200:
            raise LLMError(f"Groq API returned HTTP {response.status_code}: {response.text}")
            
        data = response.json()
        image_prompt = data["choices"][0]["message"]["content"].strip()
        if not image_prompt:
            raise LLMError("Groq returned an empty prompt response.")
            
        # Clean up quotes
        image_prompt = image_prompt.replace('"', '').replace('\n', ' ')
        logger.info("Successfully generated image prompt using Groq.")
        return image_prompt
    except Exception as e:
        logger.error(f"Groq image prompt generation error: {str(e)}")
        raise LLMError(f"Groq API failed to generate image prompt: {str(e)}")

def generate_search_keywords(caption: str) -> str:
    """
    Generates 2-3 common, generic English keywords representing the core business/topic 
    of the caption to be used for stock photo searches (e.g. 'office, laptop' or 'home theater').
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise LLMError("Groq API key is missing. Please set GROQ_API_KEY in your environment.")
        
    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    api_url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = (
        "Based on the following marketing caption, write exactly 2 to 3 very common, simple, generic English keywords "
        "that represent the core subject, industry, or visual setting of the campaign. "
        "These keywords will be used to search for a stock photo on Flickr. "
        "Do NOT include custom brand names (like 'ContentFlow', 'Netflix', etc.), tech jargon, or visual styles (like 'neon', 'cityscape'). "
        "Only output common, generic nouns separated by commas (e.g. 'office, laptop' or 'movie, television' or 'coffee, cafe'). "
        "Do not include quotes, introductory text, or explanations. Just return the comma-separated keywords.\n\n"
        f"Marketing Caption: {caption}"
    )
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 30
    }
    
    logger.info("Generating semantic stock search keywords using Groq...")
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=20)
        if response.status_code != 200:
            raise LLMError(f"Groq API returned HTTP {response.status_code}: {response.text}")
            
        data = response.json()
        keywords = data["choices"][0]["message"]["content"].strip()
        if not keywords:
            raise LLMError("Groq returned empty keywords.")
            
        # Clean and format
        keywords = keywords.replace('"', '').replace("'", '').replace('\n', ' ').strip().lower()
        # Ensure it only contains letters, commas, and spaces
        keywords = ''.join(c for c in keywords if c.isalpha() or c in [',', ' '])
        # Format as a clean comma-separated list of words
        cleaned_words = [w.strip() for w in keywords.split(',') if len(w.strip()) > 2]
        return ",".join(cleaned_words[:3])
    except Exception as e:
        logger.error(f"Groq keywords generation error: {str(e)}")
        # Simple fallback
        return "marketing"
