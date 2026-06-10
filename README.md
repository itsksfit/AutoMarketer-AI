# AutoMarketer AI

AutoMarketer AI is a production-ready, full-stack marketing automation application. By providing a single website URL, the application scrapes the webpage, extracts its core brand messaging, uses Google Gemini to generate a professional marketing caption and a structured image-generation prompt, renders a premium promotional graphic using Hugging Face's Image Generation models, and saves the complete campaign data in MongoDB.

The application features a modern, responsive dashboard with a premium dark-mode aesthetic, loading state trackers, copy-to-clipboard actions, and a history feed of previous campaigns.

---

## Technical Stack
- **Backend**: FastAPI (Python ASGI framework)
- **Database**: MongoDB Atlas or Local MongoDB (Asynchronous querying via Motor)
- **Copywriting LLM**: Google Gemini API (`gemini-1.5-flash`)
- **Image Generation**: Hugging Face Inference API (`black-forest-labs/FLUX.1-schnell`)
- **Scraper**: Requests + BeautifulSoup4 (with user-agent headers and graceful fallbacks)
- **Frontend**: Clean Vanilla HTML5, CSS3 (Glassmorphism & animations), and JavaScript (ES6 Fetch)

---

## Getting Started

### 1. Prerequisites
- **Python**: version `3.9` or higher.
- **MongoDB**: A running local MongoDB instance or a MongoDB Atlas connection string.
- **API Keys**:
  - Google Gemini API key (obtain from [Google AI Studio](https://aistudio.google.com/))
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
   MONGODB_URI=mongodb://localhost:27017/automarketer
   GEMINI_API_KEY=your_actual_gemini_api_key
   HF_API_KEY=your_actual_hugging_face_token
   HF_IMAGE_MODEL=black-forest-labs/FLUX.1-schnell
   ```

### 4. Running the Application
Start the FastAPI backend server using Uvicorn:
```bash
uvicorn main:app --reload
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
    "image_prompt": "Sleek financial technology interface on modern laptop screen, dark navy background, glowing violet light beams, professional digital art style, high contrast.",
    "image_url": "/images/campaign_f78a2e1d.png",
    "created_at": "2026-06-09T23:45:00Z"
  }
  ```
- **Caching Feature**: If the same URL is requested within 5 minutes, the endpoint returns the cached campaign from MongoDB directly, preventing redundant API calls and conserving token credits.

### `GET /campaigns`
Retrieves a list of all historically generated campaigns, sorted by newest first.

- **Response**:
  ```json
  [
    {
      "campaign_id": "60c72b2f9b1d8e23f0c3d9a1",
      "url": "https://stripe.com",
      "page_title": "Stripe | Financial Infrastructure...",
      "caption": "...",
      "image_prompt": "...",
      "image_url": "/images/campaign_f78a2e1d.png",
      "created_at": "2026-06-09T23:45:00Z"
    }
  ]
  ```

### `GET /campaigns/{id}`
Retrieves complete data for a specific campaign, including its original scraped webpage content.

---

## Codebase Architecture
- `main.py`: Entry point for FastAPI. Sets up static mounting, custom middleware exception handling, logging formats, and routing endpoints.
- `database.py`: Manages the MongoDB connection pool (via Motor client) and handles document inserts, history lookups, and duplicate detection.
- `scraper.py`: Extracts the main textual content and title from webpages using Requests and BeautifulSoup. Implements failure-tolerance to return valid metadata if a request times out.
- `llm.py`: Connects to Google's Gemini SDK. Contains copywriting prompts to generate captions and image prompt specifications.
- `image_generator.py`: Calls the Hugging Face text-to-image Inference API, handles loading-state retries (HTTP 503), and writes binary image bytes to the local disk.
- `models.py`: Pydantic validation schemas for strong typing, API responses, and database mappings.
