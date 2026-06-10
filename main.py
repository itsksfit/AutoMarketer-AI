import os
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Import local modules
from models import CampaignRequest, CampaignResponse
from database import (
    check_connection,
    check_duplicate_campaign,
    insert_campaign,
    get_all_campaigns,
    get_campaign_by_id,
    delete_campaign_by_id,
    DatabaseError
)
from scraper import scrape_website
from llm import generate_marketing_caption, generate_image_prompt, generate_search_keywords, LLMError
from image_generator import generate_and_save_image, ImageGeneratorError

# Load environment variables
load_dotenv()

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("automarketer.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("automarketer")

app = FastAPI(
    title="AutoMarketer AI API",
    description="Automated digital marketing campaigns using Groq and Hugging Face",
    version="1.0.0"
)

# CORS Middleware for local/external web interface access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure required directories exist
os.makedirs("images", exist_ok=True)
os.makedirs("static", exist_ok=True)

# Mount static files
app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup_db_client():
    logger.info("AutoMarketer AI Application is starting up...")
    # Verify database connection
    connected = await check_connection()
    if not connected:
        logger.error("WARNING: MongoDB server is offline or unreachable. Database dependent endpoints will fail.")
    else:
        logger.info("MongoDB initialized and connected successfully.")

@app.exception_handler(DatabaseError)
async def database_exception_handler(request, exc):
    logger.error(f"DB Exception handler caught: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": f"Database Connection Error: {str(exc)}"}
    )

@app.exception_handler(LLMError)
async def llm_exception_handler(request, exc):
    logger.error(f"LLM Exception handler caught: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": f"LLM Generation Error: {str(exc)}"}
    )

@app.exception_handler(ImageGeneratorError)
async def image_generator_exception_handler(request, exc):
    logger.error(f"Image Gen Exception handler caught: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": f"Image Generation Error: {str(exc)}"}
    )

@app.get("/")
async def read_index():
    """Redirects the root URL to the static dashboard page."""
    return RedirectResponse(url="/static/index.html")

@app.post("/generate-campaign", response_model=CampaignResponse)
async def generate_campaign(payload: CampaignRequest):
    """
    Scrapes the target URL, extracts page content, generates marketing caption and prompt 
    via Google Gemini, generates a custom campaign image via Hugging Face, and stores campaign details.
    
    Includes a 5-minute duplicate check window.
    """
    target_url = payload.url
    logger.info(f"Received campaign generation request for URL: {target_url}")
    
    # 1. Prevent duplicate campaign generation within 5 minutes
    try:
        duplicate = await check_duplicate_campaign(target_url, window_minutes=5)
        if duplicate:
            logger.info(f"Duplicate found within 5 minutes. Returning cached campaign '{duplicate['_id']}'")
            return CampaignResponse(
                campaign_id=duplicate["_id"],
                url=duplicate["url"],
                page_title=duplicate["page_title"],
                caption=duplicate["marketing_caption"],
                image_prompt=duplicate["image_prompt"],
                image_url=duplicate["generated_image_path"],
                created_at=duplicate["created_at"]
            )
    except DatabaseError as e:
        # If database is down, we log and proceed without cache check (or fail if production strictly requires DB)
        logger.warning(f"Database error during duplicate check: {str(e)}. Proceeding with generation.")

    # 2. Scrape the website
    scrape_result = scrape_website(target_url)
    # The scraping utility returns a fallback structured content dict if network fails, so it doesn't crash.
    
    # 3. Generate marketing caption
    caption = generate_marketing_caption(scrape_result["content"])
    
    # 4. Generate image prompt from the caption
    image_prompt = generate_image_prompt(caption)
    
    # 5. Generate semantic stock photo keywords using Groq for fallbacks
    try:
        stock_keywords = generate_search_keywords(caption)
    except Exception as e:
        logger.warning(f"Failed to generate stock search keywords: {str(e)}")
        stock_keywords = None
        
    # 6. Generate image from Hugging Face Inference API and save locally
    # We will pass a temporary campaign name/id hash to name the image file
    image_url = generate_and_save_image(image_prompt, images_dir="images", page_title=scrape_result["title"], stock_keywords=stock_keywords)
    
    # 6. Store campaign details in MongoDB
    campaign_doc = {
        "url": target_url,
        "page_title": scrape_result["title"],
        "scraped_content": scrape_result["content"],
        "marketing_caption": caption,
        "image_prompt": image_prompt,
        "generated_image_path": image_url,
        "created_at": datetime.utcnow()
    }
    
    try:
        campaign_id = await insert_campaign(campaign_doc)
        logger.info(f"Successfully created campaign '{campaign_id}' for {target_url}")
        
        return CampaignResponse(
            campaign_id=campaign_id,
            url=target_url,
            page_title=scrape_result["title"],
            caption=caption,
            image_prompt=image_prompt,
            image_url=image_url,
            created_at=campaign_doc["created_at"]
        )
    except DatabaseError as e:
        logger.error(f"Failed to save campaign to database: {str(e)}")
        # Raise HTTP exception since saving to DB is a core requirement of campaign workflow
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Campaign generated but database storage failed: {str(e)}"
        )

@app.get("/campaigns")
async def list_campaigns():
    """
    Returns all previous campaigns sorted by newest first.
    """
    logger.info("Fetching all campaigns from database...")
    campaigns = await get_all_campaigns()
    # Format database documents for clean JSON response
    formatted_campaigns = []
    for c in campaigns:
        formatted_campaigns.append({
            "campaign_id": c["_id"],
            "url": c["url"],
            "page_title": c["page_title"],
            "caption": c["marketing_caption"],
            "image_prompt": c["image_prompt"],
            "image_url": c["generated_image_path"],
            "created_at": c["created_at"]
        })
    return formatted_campaigns

@app.get("/campaigns/{id}")
async def get_campaign(id: str):
    """
    Returns complete campaign details.
    """
    logger.info(f"Fetching details for campaign ID: {id}")
    campaign = await get_campaign_by_id(id)
    if not campaign:
        logger.warning(f"Campaign with ID {id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign with ID {id} not found."
        )
        
    return {
        "campaign_id": campaign["_id"],
        "url": campaign["url"],
        "page_title": campaign["page_title"],
        "scraped_content": campaign["scraped_content"],
        "caption": campaign["marketing_caption"],
        "image_prompt": campaign["image_prompt"],
        "image_url": campaign["generated_image_path"],
        "created_at": campaign["created_at"]
    }

@app.delete("/campaigns/{id}")
async def delete_campaign(id: str):
    """
    Deletes the campaign and its associated image file.
    """
    logger.info(f"Received request to delete campaign ID: {id}")
    campaign = await get_campaign_by_id(id)
    if not campaign:
        logger.warning(f"Campaign with ID {id} not found for deletion.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign with ID {id} not found."
        )
    
    # Delete image file from local folder
    image_url = campaign.get("generated_image_path")
    if image_url:
        local_image_path = image_url.lstrip("/")
        if os.path.exists(local_image_path):
            try:
                os.remove(local_image_path)
                logger.info(f"Successfully deleted local image file: {local_image_path}")
            except Exception as e:
                logger.error(f"Failed to delete local image file {local_image_path}: {str(e)}")
        else:
            logger.warning(f"Image file {local_image_path} not found on disk.")
            
    # Delete from database
    deleted = await delete_campaign_by_id(id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete campaign from database."
        )
        
    logger.info(f"Successfully deleted campaign ID: {id}")
    return {"status": "success", "message": f"Campaign {id} has been deleted."}
