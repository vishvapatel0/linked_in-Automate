import os
import json
import time
import requests
import random
import re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class DataStore:
    """Simple data storage class for candidates."""
    
    def __init__(self):
        """Initialize the data store."""
        self.data_dir = "data"
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def save_candidates(self, job_id, candidates):
        """Save candidates to a JSON file."""
        filename = os.path.join(self.data_dir, f"candidates_{job_id}.json")
        with open(filename, "w") as f:
            json.dump(candidates, f, indent=2)
    
    def load_candidates(self, job_id):
        """Load candidates from a JSON file."""
        filename = os.path.join(self.data_dir, f"candidates_{job_id}.json")
        if os.path.exists(filename):
            with open(filename, "r") as f:
                return json.load(f)
        return []
    
    def save_results(self, filename, results):
        """Save results to a JSON file."""
        with open(filename, "w") as f:
            json.dump(results, f, indent=2)

class LinkedInAgent:
    """Agent for sourcing candidates from LinkedIn."""
    
    def __init__(self, data_store):
        """Initialize the LinkedIn agent."""
        self.data_store = data_store
        self.last_request_time = 0
        self.min_request_interval = 2.0  # seconds
    
    def _wait_for_rate_limit(self):
        """Wait to avoid hitting rate limits."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        
        self.last_request_time = time.time()
    
    def _get_direct_linkedin_urls(self, max_results=5):
        """Get a list of known LinkedIn profile URLs."""
        # These are real public LinkedIn profiles of people in ML/AI
        direct_urls = [
            "https://www.linkedin.com/in/andrewyng/",
            "https://www.linkedin.com/in/geoffreyhinton/",
            "https://www.linkedin.com/in/feifeili/",
            "https://www.linkedin.com/in/karpathy/",
            "https://www.linkedin.com/in/chelsea-finn-3317233a/",
            "https://www.linkedin.com/in/ilyasutskever/",
            "https://www.linkedin.com/in/demishassabis/",
            "https://www.linkedin.com/in/pieter-abbeel-91b2b42/",
            "https://www.linkedin.com/in/jeff-dean-8b212555/",
            "https://www.linkedin.com/in/oriolvinalsatienza/"
        ]
        return direct_urls[:max_results]
    
    def _process_profile(self, linkedin_url):
        """Process a single LinkedIn profile."""
        self._wait_for_rate_limit()
        
        # Use RapidAPI to get profile data
        profile_data = self._get_profile_from_rapidapi(linkedin_url)
        
        if profile_data:
            print(f"Successfully processed profile: {linkedin_url}")
            return profile_data
        else:
            print(f"Failed to process profile: {linkedin_url}")
            return None
    
    def _get_profile_from_rapidapi(self, linkedin_url):
        """Get LinkedIn profile data using the Fresh LinkedIn Profile Data API."""
        if not RAPIDAPI_KEY:
            print("No RapidAPI key provided")
            return None
        
        # Use the confirmed correct endpoint for the API
        api_url = "https://fresh-linkedin-profile-data.p.rapidapi.com/get-linkedin-profile"
        
        querystring = {"linkedin_url": linkedin_url}
        
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "fresh-linkedin-profile-data.p.rapidapi.com"
        }
        
        try:
            print(f"Fetching profile data for: {linkedin_url}")
            response = requests.get(api_url, headers=headers, params=querystring)
            
            if response.status_code == 200:
                data = response.json()
                
                # Format the profile data into our standard format
                formatted_profile = self._format_profile_data(data, linkedin_url)
                return formatted_profile
            else:
                print(f"RapidAPI request failed with status code {response.status_code}")
                if response.text:
                    print(f"Response: {response.text[:200]}...")
                return None
        except Exception as e:
            print(f"Error fetching LinkedIn profile: {e}")
            return None
    
    def _format_profile_data(self, api_data, linkedin_url):
        """Format the RapidAPI response into our standard profile format."""
        try:
            # Create a base profile structure
            profile = {
                "linkedin_url": linkedin_url,
                "name": "Unknown",
                "headline": "",
                "location": "",
                "summary": "",
                "experience": [],
                "education": [],
                "skills": []
            }
            
            # Extract profile information based on the API response structure
            # The exact structure will depend on the actual API response
            if isinstance(api_data, dict):
                # Try to extract basic profile data
                if "profile" in api_data:
                    profile_data = api_data["profile"]
                    
                    # Name
                    first_name = profile_data.get("firstName", "")
                    last_name = profile_data.get("lastName", "")
                    if first_name or last_name:
                        profile["name"] = f"{first_name} {last_name}".strip()
                    
                    # Headline and location
                    profile["headline"] = profile_data.get("headline", "")
                    profile["location"] = profile_data.get("locationName", "")
                    profile["summary"] = profile_data.get("summary", "")
                    
                    # Experience
                    if "experience" in profile_data and profile_data["experience"]:
                        for exp in profile_data["experience"]:
                            experience = {
                                "title": exp.get("title", ""),
                                "company": exp.get("companyName", ""),
                                "duration": exp.get("dateRange", ""),
                                "description": exp.get("description", "")
                            }
                            profile["experience"].append(experience)
                    
                    # Education
                    if "education" in profile_data and profile_data["education"]:
                        for edu in profile_data["education"]:
                            education = {
                                "school": edu.get("schoolName", ""),
                                "degree": edu.get("degree", ""),
                                "field": edu.get("fieldOfStudy", ""),
                                "dates": edu.get("dateRange", "")
                            }
                            profile["education"].append(education)
                    
                    # Skills
                    if "skills" in profile_data and profile_data["skills"]:
                        for skill in profile_data["skills"]:
                            if isinstance(skill, dict):
                                profile["skills"].append(skill.get("name", ""))
                            elif isinstance(skill, str):
                                profile["skills"].append(skill)
                
                # Alternate response structure
                elif "data" in api_data:
                    data = api_data["data"]
                    
                    # Name
                    profile["name"] = data.get("full_name", "")
                    
                    # Headline and location
                    profile["headline"] = data.get("headline", "")
                    
                    if "location" in data:
                        city = data["location"].get("city", "")
                        country = data["location"].get("country", "")
                        profile["location"] = f"{city}, {country}".strip(", ")
                    
                    profile["summary"] = data.get("summary", "")
                    
                    # Experience
                    if "experience" in data and data["experience"]:
                        for exp in data["experience"]:
                            experience = {
                                "title": exp.get("title", ""),
                                "company": exp.get("company", ""),
                                "duration": f"{exp.get('start_date', '')} - {exp.get('end_date', '')}".strip(" -"),
                                "description": exp.get("description", "")
                            }
                            profile["experience"].append(experience)
                    
                    # Education
                    if "education" in data and data["education"]:
                        for edu in data["education"]:
                            education = {
                                "school": edu.get("school", ""),
                                "degree": edu.get("degree", ""),
                                "field": edu.get("field_of_study", ""),
                                "dates": f"{edu.get('start_date', '')} - {edu.get('end_date', '')}".strip(" -")
                            }
                            profile["education"].append(education)
                    
                    # Skills
                    if "skills" in data and data["skills"]:
                        profile["skills"] = data["skills"]
            
            return profile
        except Exception as e:
            print(f"Error formatting profile data: {e}")
            return None
    
    def search_linkedin(self, job_description, max_results=5):
        """Skip search and use direct LinkedIn profile URLs."""
        print(f"Using direct LinkedIn profile URLs instead of search...")
        
        # Get direct LinkedIn profile URLs
        linkedin_urls = self._get_direct_linkedin_urls(max_results)
        
        # Extract profile data
        print(f"Extracting profile data from {len(linkedin_urls)} LinkedIn URLs...")
        candidates = []
        
        for url in tqdm(linkedin_urls):
            profile_data = self._process_profile(url)
            if profile_data:
                candidates.append(profile_data)
        
        print(f"Found {len(candidates)} candidate profiles.")
        return candidates
    
    def score_candidates(self, candidates, job_description):
        """Score candidates based on the job description."""
        print(f"Scoring {len(candidates)} candidates...")
        scored_candidates = []
        
        for candidate in tqdm(candidates):
            score = self._score_candidate(candidate, job_description)
            candidate["score"] = score
            scored_candidates.append(candidate)
        
        # Sort candidates by score (highest first)
        scored_candidates.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        print("Completed scoring candidates.")
        return scored_candidates
    
    def _score_candidate(self, candidate, job_description):
        """Score a candidate based on the job description."""
        if not OPENAI_API_KEY:
            # Simple rule-based scoring if no OpenAI API key
            score = 0
            
            # Skills matching
            relevant_skills = ["machine learning", "deep learning", "python", "pytorch", "tensorflow", "nlp", "transformer", "llm"]
            for skill in candidate.get("skills", []):
                skill_lower = skill.lower()
                for relevant_skill in relevant_skills:
                    if relevant_skill in skill_lower:
                        score += 1
            
            # Education scoring
            top_schools = ["stanford", "mit", "harvard", "berkeley", "cmu", "caltech"]
            relevant_degrees = ["phd", "ms", "master", "computer science", "machine learning", "ai"]
            
            for edu in candidate.get("education", []):
                school = edu.get("school", "").lower()
                degree = edu.get("degree", "").lower()
                
                # Check school ranking
                for top_school in top_schools:
                    if top_school in school:
                        score += 2
                        break
                
                # Check degree relevance
                for relevant_degree in relevant_degrees:
                    if relevant_degree in degree:
                        score += 1
            
            # Experience scoring
            top_companies = ["google", "meta", "facebook", "microsoft", "apple", "openai", "deepmind", "nvidia"]
            relevant_titles = ["machine learning", "ml", "ai", "research", "scientist", "engineer"]
            
            for exp in candidate.get("experience", []):
                company = exp.get("company", "").lower()
                title = exp.get("title", "").lower()
                
                # Check company prestige
                for top_company in top_companies:
                    if top_company in company:
                        score += 2
                        break
                
                # Check title relevance
                for relevant_title in relevant_titles:
                    if relevant_title in title:
                        score += 1
            
            # Cap score at 10
            return min(10, score)
        else:
            # Use OpenAI API for scoring
            import openai
            openai.api_key = OPENAI_API_KEY
            
            prompt = f"""
            Rate this candidate for a Machine Learning Research Engineer role on a scale of 1-10:
            
            Job Description:
            {job_description}
            
            Candidate Profile:
            - Name: {candidate.get('name', '')}
            - Current role: {candidate.get('headline', '')}
            - Location: {candidate.get('location', '')}
            - Summary: {candidate.get('summary', '')}
            
            Experience:
            {json.dumps(candidate.get('experience', []), indent=2)}
            
            Education:
            {json.dumps(candidate.get('education', []), indent=2)}
            
            Skills:
            {', '.join(candidate.get('skills', []))}
            
            Provide a score from 1-10 in this format: "Score: X"
            """
            
            try:
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "system", "content": "You are a technical recruiter specializing in machine learning roles."},
                              {"role": "user", "content": prompt}]
                )
                
                response_text = response.choices[0].message.content
                
                # Extract score using regex
                import re
                score_match = re.search(r"Score:\s*(\d+(?:\.\d+)?)", response_text, re.IGNORECASE)
                if score_match:
                    return float(score_match.group(1))
                else:
                    return 5.0  # Default score
            except Exception as e:
                print(f"Error using OpenAI API: {e}")
                return 5.0  # Default score
    
    def generate_outreach(self, candidates, job_description):
        """Generate personalized outreach messages for candidates."""
        print(f"Generating outreach messages for {len(candidates)} candidates...")
        messages = []
        
        for candidate in candidates:
            message = self._generate_outreach_message(candidate, job_description)
            messages.append({
                "candidate": candidate["name"],
                "linkedin_url": candidate["linkedin_url"],
                "message": message
            })
        
        return messages
    
    def _generate_outreach_message(self, candidate, job_description):
        """Generate a personalized outreach message."""
        if not OPENAI_API_KEY:
            # Simple template-based message if no OpenAI API key
            name = candidate.get("name", "").split(" ")[0]
            headline = candidate.get("headline", "")
            experience = candidate.get("experience", [])[0] if candidate.get("experience") else {}
            
            message = f"""
            Hi {name},
            
            I came across your profile and was impressed by your background as {headline}.
            
            I'm reaching out because we're looking for a Machine Learning Research Engineer to join our team at Windsurf (the company behind Codeium). The role involves training large language models for code generation.
            
            Your experience as {experience.get('title', '')} at {experience.get('company', '')} seems highly relevant. We're offering $140-300k + equity for this role in Mountain View, CA.
            
            Would you be open to a 15-minute chat about this opportunity?
            
            Best regards,
            [Recruiter Name]
            """
            
            return message.strip()
        else:
            # Use OpenAI API for personalized message
            import openai
            openai.api_key = OPENAI_API_KEY
            
            prompt = f"""
            Create a personalized LinkedIn outreach message to this candidate for a Machine Learning Research Engineer role:
            
            Job Description:
            {job_description}
            
            Candidate Profile:
            - Name: {candidate.get('name', '')}
            - Current role: {candidate.get('headline', '')}
            - Location: {candidate.get('location', '')}
            - Experience: {json.dumps(candidate.get('experience', [])[:2], indent=2)}
            - Education: {json.dumps(candidate.get('education', [])[:2], indent=2)}
            - Skills: {', '.join(candidate.get('skills', [])[:5])}
            
            Requirements:
            1. Use their first name only
            2. Keep the message under 150 words
            3. Mention specific aspects of their background relevant to this ML research role
            4. Include the salary range ($140-300k + equity)
            5. Mention the location (Mountain View, CA)
            6. Ask for a 15-minute chat
            7. Sign as "[Recruiter Name]"
            """
            
            try:
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "system", "content": "You are a technical recruiter specializing in machine learning roles."},
                              {"role": "user", "content": prompt}]
                )
                
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"Error using OpenAI API: {e}")
                return self._generate_outreach_message_template(candidate)
    
    def _generate_outreach_message_template(self, candidate):
        """Generate a template outreach message."""
        name = candidate.get("name", "").split(" ")[0]
        headline = candidate.get("headline", "")
        
        message = f"""
        Hi {name},

        I came across your profile and was impressed by your background as {headline}.

        I'm reaching out because we're looking for a Machine Learning Research Engineer to join our team at Windsurf (Codeium). The role involves training large language models for code generation.

        We're offering $140-300k + equity for this role in Mountain View, CA.

        Would you be open to a 15-minute chat about this opportunity?

        Best regards,
        [Recruiter Name]
        """
        
        return message.strip()

def main(args):
    """Main function."""
    # Default job description
    job_description = """
    Software Engineer, ML Research at Windsurf (Codeium)
    
    About the Role:
    As a Software Engineer on our ML Research team, you will train large language models to generate and understand code.
    
    Requirements:
    - Strong programming skills, particularly in Python
    - Experience with PyTorch, TensorFlow, or other deep learning frameworks
    - Understanding of transformer models and large language models
    - Background in machine learning, especially NLP
    - BS/MS/PhD in Computer Science or related field
    
    Location: Mountain View, CA (hybrid)
    Salary: $140,000 - $300,000 + equity
    """
    
    # Create a unique job ID
    job_id = "ml_research"
    
    # Initialize data store
    data_store = DataStore()
    
    # Initialize agent
    agent = LinkedInAgent(data_store=data_store)
    
    # Process job
    max_results = args.max if hasattr(args, 'max') else 5
    top_n = args.top if hasattr(args, 'top') else 2
    
    print(f"Processing job with max {max_results} candidates...")
    
    # Search for LinkedIn profiles
    candidates = agent.search_linkedin(job_description, max_results=max_results)
    
    # Score candidates
    scored_candidates = agent.score_candidates(candidates, job_description)
    
    # Generate outreach messages for top candidates
    top_candidates = scored_candidates[:top_n]
    messages = agent.generate_outreach(top_candidates, job_description)
    
    # Print results
    print("\n===== CANDIDATE RESULTS =====\n")
    print(f"Found {len(scored_candidates)} candidates.")
    print("\nTop Candidates:")
    
    for i, candidate in enumerate(top_candidates, 1):
        print(f"{i}. {candidate['name']} - Score: {candidate['score']}")
        print(f"   {candidate['headline']}")
        print(f"   URL: {candidate['linkedin_url']}")
        print()
    
    print("===== OUTREACH MESSAGES =====\n")
    
    for i, msg in enumerate(messages, 1):
        print(f"Message for: {msg['candidate']}")
        print(f"LinkedIn: {msg['linkedin_url']}")
        print(f"{msg['message']}")
        print()
    
    # Save results
    results = {
        "candidates": scored_candidates,
        "messages": messages
    }
    
    output_file = args.output if hasattr(args, 'output') else "results.json"
    
    # Convert to JSON-serializable format
    serializable_results = {
        "candidates": [{k: v for k, v in c.items() if k != 'raw_data'} for c in results["candidates"]],
        "messages": results["messages"]
    }
    
    data_store.save_results(output_file, serializable_results)
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="LinkedIn Sourcing Agent")
    parser.add_argument("--max", type=int, default=5, help="Maximum number of candidates to retrieve")
    parser.add_argument("--top", type=int, default=2, help="Number of top candidates to generate outreach messages for")
    parser.add_argument("--output", type=str, default="results.json", help="Output file name")
    
    args = parser.parse_args()
    
    main(args)