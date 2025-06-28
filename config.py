import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# LinkedIn Settings
LINKEDIN_USERNAME = os.getenv("LINKEDIN_USERNAME")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

# Search Settings
MAX_SEARCH_RESULTS = 20
RESULTS_PER_PAGE = 10
SEARCH_DELAY = 2  # Delay between searches in seconds

# Scoring Weights
SCORING_WEIGHTS = {
    "education": 0.20,
    "career_trajectory": 0.20,
    "company_relevance": 0.15,
    "experience_match": 0.25,
    "location_match": 0.10,
    "tenure": 0.10
}

# Database Settings
DB_PATH = "data/candidates.sqlite"

# Top companies in ML/AI
TOP_ML_COMPANIES = [
    "Google", "DeepMind", "OpenAI", "Microsoft", "Meta", "Apple", 
    "Amazon", "Anthropic", "Inflection AI", "Hugging Face", "Cohere",
    "Stability AI", "Midjourney", "GitHub", "Cursor", "Replit",
    "Databricks", "Scale AI", "Nvidia", "Intel", "IBM", "Salesforce",
    "Adobe", "Twitter", "LinkedIn", "Snapchat", "TikTok", "Netflix",
    "Uber", "Lyft", "Airbnb", "Spotify", "Pinterest", "Stripe",
    "Waymo", "Tesla", "Cruise", "Aurora"
]

# Top universities for CS/AI
TOP_UNIVERSITIES = [
    "MIT", "Stanford", "Carnegie Mellon", "UC Berkeley", "Harvard",
    "Princeton", "California Institute of Technology", "ETH Zurich",
    "University of Oxford", "University of Cambridge", "Imperial College London",
    "University of Washington", "Georgia Tech", "University of Illinois",
    "University of Toronto", "University of Montreal", "University of Michigan",
    "Cornell University", "Columbia University", "University of Pennsylvania",
    "UCLA", "UCSD", "NYU", "University of Texas", "University of Wisconsin"
]

# ML/AI Skills
ML_AI_SKILLS = [
    "machine learning", "deep learning", "artificial intelligence", "neural networks", 
    "natural language processing", "NLP", "computer vision", "reinforcement learning",
    "transformer models", "GPT", "BERT", "large language models", "LLMs", "PyTorch", 
    "TensorFlow", "Keras", "JAX", "scikit-learn", "data science", "AI research",
    "model training", "fine-tuning", "prompt engineering", "vector embeddings",
    "transfer learning", "generative AI", "diffusion models", "multimodal models"
]

# Location for Windsurf job
TARGET_LOCATION = "Mountain View"
NEARBY_LOCATIONS = ["San Francisco", "Palo Alto", "Menlo Park", "Sunnyvale", 
                   "Santa Clara", "San Jose", "Redwood City", "Cupertino"]