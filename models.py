from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
import re

class CampaignRequest(BaseModel):
    url: str = Field(..., description="The website URL to generate the campaign from")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        # Simple URL regex validation
        regex = re.compile(
            r'^(?:http|ftp)s?://' # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain...
            r'localhost|' # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
            r'(?::\d+)?' # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not re.match(regex, v):
            raise ValueError("Invalid URL format. URL must start with http:// or https://")
        return v

class CampaignResponse(BaseModel):
    campaign_id: str = Field(..., description="Unique ID of the generated campaign")
    url: str = Field(..., description="The source website URL")
    page_title: str = Field(..., description="Scraped page title")
    caption: str = Field(..., description="AI-generated marketing caption")
    image_prompt: str = Field(..., description="AI-generated image prompt")
    image_url: str = Field(..., description="Local path/URL to the generated image")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")

class CampaignDetail(BaseModel):
    id: str = Field(..., alias="_id", description="MongoDB ObjectId as string")
    url: str
    page_title: str
    scraped_content: str
    marketing_caption: str
    image_prompt: str
    generated_image_path: str
    created_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
