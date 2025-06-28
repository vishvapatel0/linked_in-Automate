import os
import re
import json
import time
import random
import requests
import string
from collections import Counter
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
SERP_API_KEY = os.getenv("SERPAPI_KEY")

def get_random_user_agent():
    """Generate a random user agent for web requests."""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/96.0.1054.43 Safari/537.36"
    ]
    return random.choice(user_agents)

def extract_keywords_from_job(job_description):
    """Extract key technical and domain-specific terms from job description."""
    # Clean text
    text = job_description.lower()
    text = re.sub(r'[^\w\s]', ' ', text)  # Replace punctuation with space
    
    # Tokenize
    words = text.split()
    
    # Remove stopwords
    stopwords = set([
        'the', 'and', 'to', 'of', 'a', 'in', 'for', 'with', 'on', 'at', 'from', 
        'by', 'about', 'as', 'into', 'like', 'through', 'after', 'over', 'between',
        'out', 'is', 'am', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
        'had', 'do', 'does', 'did', 'but', 'if', 'or', 'because', 'as', 'until', 'while',
        'that', 'this', 'these', 'those', 'then', 'than', 'when', 'where', 'why', 'how',
        'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such',
        'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'too', 'very', 'can', 'will',
        'just', 'should', 'now', 'role', 'we', 'our', 'you', 'your'
    ])
    
    filtered_words = [word for word in words if word not in stopwords and len(word) > 2]
    
    # Count word frequency
    word_counts = Counter(filtered_words)
    
    # Extract technical terms and skills (usually multi-word)
    technical_terms = [
        # Programming languages
        'python', 'javascript', 'java', 'c++', 'typescript', 'ruby', 'go', 'rust', 'php', 'scala', 'kotlin',
        # Frameworks
        'react', 'angular', 'vue', 'django', 'flask', 'spring', 'node', 'express', 'laravel', 'rails',
        # Data science/ML
        'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'keras', 'sklearn', 'pandas', 'numpy',
        'neural networks', 'nlp', 'computer vision', 'reinforcement learning', 'data mining', 'statistics',
        # Cloud
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'cloud',
        # Databases
        'sql', 'nosql', 'mongodb', 'postgresql', 'mysql', 'oracle', 'cassandra', 'redis', 'elasticsearch',
        # Other tech skills
        'rest', 'api', 'microservices', 'ci/cd', 'git', 'agile', 'scrum', 'devops', 'testing'
    ]
    
    # Check for technical terms in text
    found_terms = []
    for term in technical_terms:
        if term in text:
            found_terms.append(term)
    
    # Get top frequent words
    top_words = [word for word, count in word_counts.most_common(20) if count > 1]
    
    # Combine found technical terms with top words
    keywords = list(set(found_terms + top_words))
    
    return keywords[:15]  # Return top 15 keywords

def parse_job_requirements(job_description):
    """Extract key requirements from a job description."""
    # Extract title
    title = ""
    first_line = job_description.strip().split("\n")[0]
    if ":" in first_line:
        title = first_line.split(":", 1)[0].strip()
    elif "," in first_line:
        title = first_line.split(",", 1)[0].strip()
    else:
        title = first_line
    
    # Extract skills using bullet points or dashes
    skills = []
    lines = job_description.split("\n")
    in_requirements = False
    
    for line in lines:
        line = line.strip()
        
        # Check if we're in the requirements section
        if re.search(r'^(requirements|qualifications|skills|what you.ll need).*:', line, re.IGNORECASE):
            in_requirements = True
            continue
        
        # Check for another section header to stop requirements
        if in_requirements and line and line[0].isupper() and ':' in line:
            in_requirements = False
        
        # Extract skill from bullet points or dashes
        if in_requirements and (line.startswith('-') or line.startswith('•')):
            skill = line.lstrip('-•').strip()
            if skill:
                skills.append(skill)
    
    # If no bullet-point skills found, try regex approach
    if not skills:
        skills_pattern = r"(?:skills|requirements|qualifications|experience with)[:]\s*(.*?)(?:\n\n|\n[A-Z]|\Z)"
        skills_match = re.search(skills_pattern, job_description, re.IGNORECASE | re.DOTALL)
        
        if skills_match:
            skills_text = skills_match.group(1)
            skills = [s.strip("- •") for s in skills_text.split("\n") if s.strip()]
    
    # Extract location
    location = ""
    location_match = re.search(r"(?:location|location:)[\s:]+([^\.]+)", job_description, re.IGNORECASE)
    if location_match:
        location = location_match.group(1).strip()
    
    # Extract education
    education = ""
    education_match = re.search(r"(?:education|degree)[\s:]+([^\.]+)", job_description, re.IGNORECASE)
    if education_match:
        education = education_match.group(1).strip()
    
    return {
        "title": title,
        "skills": skills,
        "location": location,
        "education": education
    }

def extract_linkedin_urls_from_google(search_query, num_results=10):
    """Use Google search to find LinkedIn profiles with improved extraction."""
    # Add LinkedIn site restriction to query
    if "site:linkedin.com/in" not in search_query.lower():
        encoded_query = quote_plus(f"site:linkedin.com/in/ {search_query}")
    else:
        encoded_query = quote_plus(search_query)
    
    search_url = f"https://www.google.com/search?q={encoded_query}&num={num_results*2}"
    
    print(f"Searching Google for LinkedIn profiles: {search_query}")
    
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.google.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        response = requests.get(search_url, headers=headers, timeout=15)
        time.sleep(random.uniform(1.0, 2.0))  # Wait to avoid rate limiting
        
        if response.status_code != 200:
            print(f"Google search failed with status code {response.status_code}")
            return []
        
        # Use regex to extract LinkedIn URLs
        linkedin_urls = []
        pattern = r'https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+(?:/[a-zA-Z0-9_-]+)?'
        matches = re.findall(pattern, response.text)
        
        for url in matches:
            if url not in linkedin_urls:
                clean_url = url.split('&')[0].split('?')[0]  # Remove query parameters
                linkedin_urls.append(clean_url)
                print(f"Found LinkedIn URL from Google: {clean_url}")
        
        return linkedin_urls[:num_results]
    
    except Exception as e:
        print(f"Error during Google search: {str(e)}")
        return []

def extract_linkedin_urls_from_serp(search_query, num_results=10):
    """Use Serper API to find LinkedIn profiles based on job requirements."""
    if not SERP_API_KEY:
        print("No Serper API key provided")
        return []
    
    # Add LinkedIn site restriction to query
    if "site:linkedin.com/in" not in search_query.lower():
        query = f"site:linkedin.com/in/ {search_query}"
    else:
        query = search_query
    
    url = "https://google.serper.dev/search"
    
    payload = json.dumps({
        "q": query,
        "num": num_results * 2  # Request more results than needed
    })
    
    headers = {
        'X-API-KEY': SERP_API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"Searching with Serper API: {query}")
        response = requests.post(url, headers=headers, data=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Serper API response received. Status: {data.get('searchParameters', {}).get('status', 'unknown')}")
            
            linkedin_urls = []
            
            # Debug: print full response structure
            print(f"Serper API response keys: {list(data.keys())}")
            
            # Process organic results
            if "organic" in data:
                print(f"Found {len(data['organic'])} organic results")
                
                for result in data["organic"]:
                    link = result.get("link", "")
                    title = result.get("title", "")
                    
                    print(f"Examining result: {title[:30]}... - {link}")
                    
                    if "linkedin.com/in/" in link:
                        clean_url = link.split('?')[0]  # Remove query parameters
                        if clean_url not in linkedin_urls:
                            linkedin_urls.append(clean_url)
                            print(f"Found LinkedIn URL from Serper: {clean_url}")
            else:
                print("No 'organic' results found in Serper API response")
                # Save debug data
                with open("serper_debug.json", "w") as f:
                    json.dump(data, f, indent=2)
                print("Debug data saved to serper_debug.json")
            
            return linkedin_urls[:num_results]
        else:
            print(f"Serper API request failed: {response.status_code}")
            if response.text:
                print(f"Response: {response.text[:200]}...")
            return []
    
    except Exception as e:
        print(f"Error using Serper API: {e}")
        return []
    
def extract_basic_linkedin_data_from_html(linkedin_url):
    """Extract basic data from LinkedIn profile page."""
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        response = requests.get(linkedin_url, headers=headers, timeout=15)
        time.sleep(random.uniform(1.0, 2.0))  # Wait to avoid rate limiting
        
        if response.status_code != 200:
            print(f"Failed to access LinkedIn profile: {linkedin_url}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title for name and headline
        title_tag = soup.find('title')
        name = "Unknown"
        headline = ""
        
        if title_tag:
            title_text = title_tag.text
            
            # Title usually has format: "Name - Headline | LinkedIn"
            if ' - ' in title_text and ' | LinkedIn' in title_text:
                name_headline = title_text.split(' | LinkedIn')[0]
                name_parts = name_headline.split(' - ', 1)
                
                if len(name_parts) >= 1:
                    name = name_parts[0].strip()
                
                if len(name_parts) >= 2:
                    headline = name_parts[1].strip()
        
        # Try to extract additional data from meta tags
        location = ""
        skills = []
        
        # Meta description may contain location
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            desc_content = meta_desc.get('content')
            # Location is often in the format "... at [Company] · [Location]"
            if " · " in desc_content:
                location_part = desc_content.split(" · ")[-1].split(" | ")[0]
                location = location_part.strip()
        
        # Create basic profile object
        profile = {
            "name": name,
            "headline": headline,
            "location": location,
            "linkedin_url": linkedin_url,
            "experience": [],
            "education": [],
            "skills": skills
        }
        
        print(f"Extracted basic profile data for {name}")
        return profile
    
    except Exception as e:
        print(f"Error extracting LinkedIn data from HTML: {str(e)}")
        return None