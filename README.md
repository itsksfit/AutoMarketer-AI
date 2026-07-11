### AutoMarketer AI

🚀 **Live Demo**: [https://automarketer-ai.onrender.com/](https://automarketer-ai.onrender.com/)

AutoMarketer AI is a production-ready, full-stack marketing automation application. By providing a single website URL, the application scrapes the webpage, extracts its core brand messaging, uses the **Groq API** to generate a professional marketing caption and a structured image-generation prompt, renders a premium promotional graphic using Hugging Face's Image Generation models (with automatic stock photo fallbacks), and saves the complete campaign data in MongoDB.

The application features a modern, responsive dashboard with a premium dark-mode glassmorphic aesthetic, loading state trackers, copy-to-clipboard actions, and a history feed of previous campaigns.

---

## Technical Stack
- **Backend**: FastAPI (Python ASGI framework)
- **Database**: MongoDB Atlas or Local MongoDB (Asynchronous querying via Motor) with local JSON file fallback (`campaigns_mock_db.json`)
- **Copywriting LLM**: Groq Chat Completions API (`llama-3.3-70b-versatile`)
- **Image Generation**: Hugging Face Inference API (`black-forest-labs/FLUX.1-schnell`)
- **Fallback Stock Search**: LoremFlickr API (semantic matching using extracted LLM keywords) and Picsum Photos API
- **Scraper**: Requests + BeautifulSoup4 (with user-agent headers and graceful fallbacks)
- **Frontend**: Clean Vanilla HTML5, CSS3 (Glassmorphism & animations), and JavaScript (ES6 Fetch)

---

## Getting Started

### 1. Prerequisites
- **Python**: version `3.9` or higher.
- **MongoDB**: A running local MongoDB instance or a MongoDB Atlas connection string.
- **API Keys**:
  - Groq API key (obtain from [Groq Console](https://console.groq.com/))
  - Hugging Face Inference Token (obtain from [Hugging Face settings](https://huggingface.co/settings/tokens))

### 2. Installation
1. Clone or navigate to the project directory:
   ```bash
   cd /path/to/project
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Configuration
1. Copy the environment template to create a `.env` file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your API credentials:
   ```env
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/database
   GROQ_API_KEY=your_actual_groq_api_key
   GROQ_MODEL=llama-3.3-70b-versatile
   HF_API_KEY=your_actual_hugging_face_token
   HF_IMAGE_MODEL=black-forest-labs/FLUX.1-schnell
   ```

### 4. Running the Application
Start the FastAPI backend server using Uvicorn:
```bash
python3 -m uvicorn main:app --reload
```
The application will launch locally:
- **Web Interface (Dashboard)**: [http://localhost:8000/](http://localhost:8000/)
- **Swagger API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## API Endpoints

### `POST /generate-campaign`
Accepts a URL, runs the marketing generation workflow, saves results to the database, and returns the asset details.

- **Request Body**:
  ```json
  {
    "url": "https://stripe.com"
  }
  ```
- **Response**:
  ```json
  {
    "campaign_id": "60c72b2f9b1d8e23f0c3d9a1",
    "url": "https://stripe.com",
    "page_title": "Stripe | Financial Infrastructure for the Internet",
    "caption": "Accelerate your digital growth with Stripe's robust financial tools. Seamlessly integrate global payments to scale your operations effortlessly.",
    "image_prompt": "A clean, modern office workspace with a laptop displaying financial charts on Stripe software, surrounded by notebooks, a cup of coffee, and soft warm lighting.",
    "image_url": "/images/campaign_f78a2e1d.png",
    "created_at": "2026-06-10T10:30:00Z"
  }
  ```
- **Caching Feature**: If the same URL is requested within 5 minutes, the endpoint returns the cached campaign directly, preventing redundant API calls and conserving token credits.

### `GET /campaigns`
Retrieves a list of all historically generated campaigns, sorted by newest first.

### `GET /campaigns/{id}`
Retrieves complete data for a specific campaign, including its original scraped webpage content.

---

## Codebase Architecture
- `main.py`: Entry point for FastAPI. Sets up static mounting, custom middleware exception handling, logging formats, and routing endpoints.
- `database.py`: Manages the MongoDB connection pool (via Motor client) and handles document inserts, history lookups, duplicate detection, and offline JSON mock fallbacks.
- `scraper.py`: Extracts the main textual content and title from webpages using Requests and BeautifulSoup.
- `llm.py`: Connects to Groq API to generate marketing captions, art direction image prompts, and fallback stock search terms.
- `image_generator.py`: Coordinates Hugging Face image generation and handles retries, falling back to LoremFlickr, Picsum Photos, and SVG vector graphics respectively on connectivity blocks.
- `models.py`: Pydantic validation schemas for typing, requests, and responses.
