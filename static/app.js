// Global variables to store current state
const API_BASE = window.location.protocol === 'file:' ? 'http://localhost:8000' : '';
let campaignsList = [];
let activeCampaignId = null;

// DOM Elements
const generatorForm = document.getElementById('generator-form');
const urlInput = document.getElementById('url-input');
const generateBtn = document.getElementById('generate-btn');
const loadingState = document.getElementById('loading-state');
const emptyState = document.getElementById('empty-state');
const resultsWorkspace = document.getElementById('results-workspace');
const imgPlaceholder = document.getElementById('img-placeholder');
const imgDisplayWrapper = document.getElementById('img-display-wrapper');
const resWebsiteTitle = document.getElementById('res-website-title');
const resWebsiteLink = document.getElementById('res-website-link');
const resCaption = document.getElementById('res-caption');
const resPrompt = document.getElementById('res-prompt');
const resImage = document.getElementById('res-image');
const downloadImageBtn = document.getElementById('download-image-btn');
const deleteCampaignBtn = document.getElementById('delete-campaign-btn');
const historyList = document.getElementById('history-list');
const historyCount = document.getElementById('history-count');
const loaderTitle = document.getElementById('loader-title');
const loaderSubtitle = document.getElementById('loader-subtitle');

// Steps elements
const steps = {
    scrape: document.getElementById('step-scrape'),
    caption: document.getElementById('step-caption'),
    prompt: document.getElementById('step-prompt'),
    image: document.getElementById('step-image')
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    fetchHistory();
    
    // Form Submission Listener
    generatorForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const url = urlInput.value.trim();
        if (url) {
            generateCampaign(url);
        }
    });

    // Delete Button Listener
    if (deleteCampaignBtn) {
        deleteCampaignBtn.addEventListener('click', () => {
            if (activeCampaignId) {
                deleteCampaign(activeCampaignId);
            }
        });
    }
});

// Toast Notification Helper
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let iconClass = 'fa-circle-info';
    if (type === 'success') iconClass = 'fa-circle-check';
    if (type === 'error') iconClass = 'fa-triangle-exclamation';
    if (type === 'warning') iconClass = 'fa-circle-exclamation';
    
    toast.innerHTML = `
        <i class="fa-solid ${iconClass} toast-icon"></i>
        <div class="toast-message">${message}</div>
    `;
    
    container.appendChild(toast);
    
    // Animate out and remove after 4 seconds
    setTimeout(() => {
        toast.classList.add('toast-out');
        toast.addEventListener('animationend', () => {
            toast.remove();
        });
    }, 4000);
}

// Copy to Clipboard Utility
async function copyText(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const textToCopy = element.innerText || element.textContent;
    try {
        await navigator.clipboard.writeText(textToCopy);
        showToast('Copied to clipboard!', 'success');
    } catch (err) {
        showToast('Failed to copy text.', 'error');
    }
}

// Fetch Campaign History
async function fetchHistory() {
    try {
        const response = await fetch(`${API_BASE}/campaigns`);
        if (!response.ok) throw new Error('Failed to fetch campaigns history.');
        
        campaignsList = await response.json();
        renderHistoryList();
    } catch (err) {
        console.error(err);
        historyList.innerHTML = `<div class="history-empty"><i class="fa-solid fa-triangle-exclamation"></i> Error loading history</div>`;
    }
}

// Render History Panel List
function renderHistoryList() {
    historyCount.textContent = campaignsList.length;
    
    if (campaignsList.length === 0) {
        historyList.innerHTML = `<div class="history-empty">No previous campaigns</div>`;
        return;
    }
    
    historyList.innerHTML = '';
    campaignsList.forEach(c => {
        const card = document.createElement('div');
        card.className = `history-card ${c.campaign_id === activeCampaignId ? 'selected' : ''}`;
        card.dataset.id = c.campaign_id;
        
        // Format date
        const date = new Date(c.created_at);
        const formattedDate = date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
        
        card.innerHTML = `
            <div class="card-title">${escapeHTML(c.page_title || 'Untitled Campaign')}</div>
            <div class="card-meta">
                <span class="card-url" title="${escapeHTML(c.url)}">${escapeHTML(cleanURLDisplay(c.url))}</span>
                <span>${formattedDate}</span>
            </div>
        `;
        
        card.addEventListener('click', () => {
            loadCampaignIntoWorkspace(c.campaign_id);
        });
        
        historyList.appendChild(card);
    });
}

// Helper to escape HTML and prevent XSS
function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, 
        tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
    );
}

// Clean url for history display
function cleanURLDisplay(url) {
    try {
        let clean = url.replace(/^(https?:\/\/)?(www\.)?/, '');
        return clean.length > 22 ? clean.substring(0, 20) + '...' : clean;
    } catch (e) {
        return url;
    }
}

// Load Campaign Details into workspace
function loadCampaignIntoWorkspace(campaignId, fallbackCampaign = null) {
    let campaign = campaignsList.find(c => c.campaign_id === campaignId);
    if (!campaign && fallbackCampaign) {
        campaign = fallbackCampaign;
    }
    if (!campaign) return;
    
    activeCampaignId = campaignId;
    
    // Highlight selected card
    document.querySelectorAll('.history-card').forEach(card => {
        if (card.dataset.id === campaignId) {
            card.classList.add('selected');
        } else {
            card.classList.remove('selected');
        }
    });
    
    // Render details
    emptyState.classList.add('hidden');
    loadingState.classList.add('hidden');
    
    resWebsiteTitle.textContent = campaign.page_title || 'Untitled Website';
    resWebsiteLink.href = campaign.url;
    resCaption.textContent = campaign.caption;
    resPrompt.textContent = campaign.image_prompt;
    const imageFullUrl = campaign.image_url.startsWith('http') ? campaign.image_url : API_BASE + campaign.image_url;
    resImage.src = imageFullUrl;
    downloadImageBtn.href = imageFullUrl;
    
    resultsWorkspace.classList.remove('hidden');
    imgPlaceholder.classList.add('hidden');
    imgDisplayWrapper.classList.remove('hidden');
}

// Progress Steps Animation Controller
function setStepState(stepName, state) {
    const el = steps[stepName];
    if (!el) return;
    
    if (state === 'active') {
        el.className = 'step active';
        el.querySelector('.step-check').innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i>';
    } else if (state === 'completed') {
        el.className = 'step completed';
        el.querySelector('.step-check').innerHTML = '<i class="fa-solid fa-circle-check"></i>';
    } else {
        el.className = 'step';
        el.querySelector('.step-check').innerHTML = '<i class="fa-regular fa-circle"></i>';
    }
}

// Generate New Campaign Trigger
async function generateCampaign(url) {
    // 1. Reset UI to loading state
    emptyState.classList.add('hidden');
    resultsWorkspace.classList.add('hidden');
    imgDisplayWrapper.classList.add('hidden');
    imgPlaceholder.classList.remove('hidden');
    loadingState.classList.remove('hidden');
    
    urlInput.disabled = true;
    generateBtn.disabled = true;
    generateBtn.querySelector('span').textContent = 'Processing...';
    
    // Initialize loading steps
    setStepState('scrape', 'active');
    setStepState('caption', 'pending');
    setStepState('prompt', 'pending');
    setStepState('image', 'pending');
    
    loaderTitle.textContent = "Analyzing Website...";
    loaderSubtitle.textContent = "Scraping content and extracting HTML structure.";

    // Track simulated step changes (in case backend is super fast or to provide smooth user visual transitions)
    let progressTimer;
    const updateProgressSubtitles = () => {
        let elapsed = 0;
        progressTimer = setInterval(() => {
            elapsed += 1;
            if (elapsed === 3) {
                setStepState('scrape', 'completed');
                setStepState('caption', 'active');
                loaderTitle.textContent = "Creating Marketing Angle...";
                loaderSubtitle.textContent = "Synthesizing main message and writing 2-sentence copy with Google Gemini.";
            } else if (elapsed === 6) {
                setStepState('caption', 'completed');
                setStepState('prompt', 'active');
                loaderTitle.textContent = "Directing AI Art Model...";
                loaderSubtitle.textContent = "Instructing Gemini to frame colors, style, and layouts for the generation prompt.";
            } else if (elapsed === 9) {
                setStepState('prompt', 'completed');
                setStepState('image', 'active');
                loaderTitle.textContent = "Rendering Image Assets...";
                loaderSubtitle.textContent = "Hugging Face Inference API is compiling diffusion models. Please wait.";
            }
        }, 1000);
    };
    
    updateProgressSubtitles();

    try {
        const response = await fetch(`${API_BASE}/generate-campaign`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url })
        });
        
        clearInterval(progressTimer);
        
        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'Failed to generate campaign.');
        }
        
        const data = await response.json();
        
        // Finalize loading indicators
        setStepState('scrape', 'completed');
        setStepState('caption', 'completed');
        setStepState('prompt', 'completed');
        setStepState('image', 'completed');
        
        showToast('Campaign generated successfully!', 'success');
        
        // Refresh history to include new item
        await fetchHistory();
        
        // Load the new campaign into the workspace
        loadCampaignIntoWorkspace(data.campaign_id, data);
        
    } catch (err) {
        clearInterval(progressTimer);
        console.error(err);
        showToast(err.message || 'An unexpected error occurred.', 'error');
        
        // Restore empty state
        loadingState.classList.add('hidden');
        emptyState.classList.remove('hidden');
        imgPlaceholder.classList.remove('hidden');
        imgDisplayWrapper.classList.add('hidden');
        
    } finally {
        urlInput.disabled = false;
        urlInput.value = '';
        generateBtn.disabled = false;
        generateBtn.querySelector('span').textContent = 'Generate Campaign';
    }
}

// Delete Campaign Handler
async function deleteCampaign(campaignId) {
    if (!confirm('Are you sure you want to delete this campaign? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/campaigns/${campaignId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'Failed to delete campaign.');
        }
        
        showToast('Campaign deleted successfully.', 'success');
        
        // Reset workspace to empty state if the deleted campaign was active
        if (activeCampaignId === campaignId) {
            activeCampaignId = null;
            resultsWorkspace.classList.add('hidden');
            imgDisplayWrapper.classList.add('hidden');
            imgPlaceholder.classList.remove('hidden');
            emptyState.classList.remove('hidden');
        }
        
        // Refresh history list
        await fetchHistory();
    } catch (err) {
        console.error(err);
        showToast(err.message || 'An unexpected error occurred while deleting the campaign.', 'error');
    }
}
