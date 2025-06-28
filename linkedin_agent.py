import os
import json
import time
import random
import requests
import re
from tqdm import tqdm
from dotenv import load_dotenv
from utils import extract_linkedin_urls_from_google, extract_linkedin_urls_from_serp, extract_basic_linkedin_data_from_html, parse_job_requirements, extract_keywords_from_job

# Load environment variables
load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class LinkedInAgent:
    """Agent for sourcing candidates from LinkedIn."""
    
    def __init__(self, data_store, use_rapidapi=True, use_serp=True):
        """Initialize the LinkedIn agent."""
        self.data_store = data_store
        self.use_rapidapi = use_rapidapi
        self.use_serp = use_serp
        self.last_request_time = 0
        self.min_request_interval = 2.0  # seconds
    
    def _wait_for_rate_limit(self):
        """Wait to avoid hitting rate limits."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        
        self.last_request_time = time.time()
    
    def _build_search_queries(self, job_requirements, job_description):
        """Build search queries based on job requirements and description."""
        # Get title, skills, location, education
        title = job_requirements.get("title", "").strip()
        skills = job_requirements.get("skills", [])
        location = job_requirements.get("location", "").strip()
        education = job_requirements.get("education", "").strip()
        
        # Extract keywords from the job description
        keywords = extract_keywords_from_job(job_description)
        
        # Determine the base job role
        base_role = title if title else "professional"
        if not title and "requirements" in job_description.lower():
            # Try to extract title from the job description
            lines = job_description.split("\n")
            for line in lines[:5]:  # Look in first 5 lines
                if ":" in line:
                    base_role = line.split(":", 1)[0].strip()
                    break
        
        # Build a list of queries
        queries = []
        
        # Add base query with title and location
        if location:
            queries.append(f"{base_role} {location}")
        else:
            queries.append(base_role)
        
        # Combine title with key skills
        key_skills = [skill for skill in skills if skill.strip()][:5]  # Top 5 skills
        for skill in key_skills:
            queries.append(f"{base_role} {skill}")
        
        # Add education-specific query
        if education:
            edu_terms = re.findall(r'\b(?:PhD|Masters?|MS|BS|BA|Bachelors?|Degree)\b', education, re.IGNORECASE)
            if edu_terms:
                for term in edu_terms:
                    queries.append(f"{base_role} {term}")
        
        # Add keyword-based queries
        for keyword in keywords[:5]:  # Use top 5 keywords
            if keyword != base_role:
                queries.append(f"{base_role} {keyword}")
        
        # Add some domain-specific variations
        if "machine learning" in job_description.lower() or "ml" in job_description.lower():
            domain_queries = [
                f"{base_role} machine learning",
                f"{base_role} deep learning",
                f"{base_role} artificial intelligence",
                f"{base_role} NLP",
                f"{base_role} neural networks"
            ]
            queries.extend(domain_queries)
        elif "software" in job_description.lower() or "developer" in job_description.lower():
            domain_queries = [
                f"{base_role} software engineer",
                f"{base_role} software developer",
                f"{base_role} programmer",
                f"{base_role} coding"
            ]
            queries.extend(domain_queries)
        elif "data" in job_description.lower() and ("science" in job_description.lower() or "analyst" in job_description.lower()):
            domain_queries = [
                f"{base_role} data scientist",
                f"{base_role} data analyst",
                f"{base_role} statistical analysis",
                f"{base_role} data visualization"
            ]
            queries.extend(domain_queries)
        elif "marketing" in job_description.lower():
            domain_queries = [
                f"{base_role} digital marketing",
                f"{base_role} marketing strategy",
                f"{base_role} SEO",
                f"{base_role} social media marketing"
            ]
            queries.extend(domain_queries)
        elif "sales" in job_description.lower():
            domain_queries = [
                f"{base_role} sales executive",
                f"{base_role} sales manager",
                f"{base_role} business development",
                f"{base_role} account executive"
            ]
            queries.extend(domain_queries)
        
        # Remove duplicates and ensure each query is unique
        unique_queries = []
        for query in queries:
            normalized = query.lower()
            if normalized not in [q.lower() for q in unique_queries]:
                unique_queries.append(query)
        
        print(f"Generated {len(unique_queries)} unique search queries based on job description")
        return unique_queries
    
    def search_linkedin(self, job_description, max_results=20):
        """Search for LinkedIn profiles matching the job description."""
        print(f"Searching for LinkedIn profiles based on job description...")
        
        # Extract job requirements
        job_requirements = parse_job_requirements(job_description)
        
        # Build search queries based on job description
        search_queries = self._build_search_queries(job_requirements, job_description)
        
        # Search for LinkedIn profiles
        linkedin_urls = set()
        
        for query in search_queries:
            print(f"Searching with query: {query}")
            
            # Try SerpAPI first if available
            if self.use_serp:
                urls = extract_linkedin_urls_from_serp(query, num_results=10)
                for url in urls:
                    linkedin_urls.add(url)
            
            # Fall back to Google search if needed
            if len(linkedin_urls) < max_results:
                self._wait_for_rate_limit()
                urls = extract_linkedin_urls_from_google(query, num_results=10)
                for url in urls:
                    linkedin_urls.add(url)
            
            # Stop if we have enough results
            if len(linkedin_urls) >= max_results:
                break
        
        # Cap at max_results
        linkedin_urls = list(linkedin_urls)[:max_results]
        
        # Extract profile data
        print(f"Extracting profile data from {len(linkedin_urls)} LinkedIn URLs...")
        candidates = self._extract_profile_data(linkedin_urls)
        
        # Filter candidates based on job relevance
        filtered_candidates = self._filter_candidates(candidates, job_description)
        
        print(f"Found {len(filtered_candidates)} relevant candidate profiles out of {len(candidates)} total profiles.")
        return filtered_candidates
    
    def _filter_candidates(self, candidates, job_description):
        """Filter candidates based on relevance to the job description."""
        if not candidates:
            print("WARNING: No candidates to filter - search returned 0 results")
            return []
            
        print(f"Filtering {len(candidates)} profiles for relevance...")
        
        # Don't filter if we already have too few candidates
        if len(candidates) <= 3:
            print("Too few candidates to filter - keeping all profiles")
            return candidates
        
        job_req = parse_job_requirements(job_description)
        job_title = job_req.get("title", "").lower()
        job_skills = [skill.lower() for skill in job_req.get("skills", [])]
        
        filtered_candidates = []
        rejected_candidates = []
        
        for candidate in candidates:
            relevance_score = 0
            candidate_name = candidate.get("name", "Unknown")
            
            # Check headline for relevance
            headline = candidate.get("headline", "").lower()
            if any(skill in headline for skill in job_skills) or job_title in headline:
                relevance_score += 2
                print(f"  + {candidate_name}: Headline matches job requirements (+2)")
            
            # Check experience for relevance
            experiences = candidate.get("experience", [])
            for exp in experiences:
                title = exp.get("title", "").lower()
                if any(skill in title for skill in job_skills) or job_title in title:
                    relevance_score += 2
                    print(f"  + {candidate_name}: Experience title matches job requirements (+2)")
                    break
            
            # Check skills for relevance
            candidate_skills = [str(skill).lower() for skill in candidate.get("skills", [])]
            skill_match = False
            for job_skill in job_skills:
                for candidate_skill in candidate_skills:
                    if job_skill in candidate_skill or candidate_skill in job_skill:
                        skill_match = True
                        relevance_score += 1
                        print(f"  + {candidate_name}: Skills match job requirements (+1)")
                        break
                if skill_match:
                    break
            
            # Always include profiles with complete information
            if experiences and candidate_skills:
                relevance_score += 1
                print(f"  + {candidate_name}: Profile has complete information (+1)")
                
            # Add candidate if they have ANY relevance or the candidate pool is small
            if relevance_score > 0 or len(candidates) <= 5:
                filtered_candidates.append(candidate)
            else:
                rejected_candidates.append(candidate)
        
        # If we filtered out everyone, return at least some of the original candidates
        if not filtered_candidates and candidates:
            print("WARNING: All candidates were filtered out. Using top 3 unfiltered candidates.")
            return candidates[:3]
        
        print(f"Filtering complete: {len(filtered_candidates)} profiles kept, {len(rejected_candidates)} profiles rejected")
        return filtered_candidates


    def _extract_profile_data(self, linkedin_urls):
        """Extract profile data from LinkedIn URLs."""
        candidates = []
        
        for url in tqdm(linkedin_urls, desc="Extracting profile data"):
            profile_data = self._process_profile(url)
            if profile_data:
                candidates.append(profile_data)
        
        return candidates
    
    def _process_profile(self, linkedin_url):
        """Process a single LinkedIn profile."""
        self._wait_for_rate_limit()
        
        # First try RapidAPI
        profile_data = None
        if self.use_rapidapi:
            print(f"Trying RapidAPI for {linkedin_url}")
            profile_data = self._get_profile_from_rapidapi(linkedin_url)
            if profile_data:
                print(f"Successfully got data from RapidAPI for {linkedin_url}")
            else:
                print(f"Failed to get data from RapidAPI for {linkedin_url}")
        
        # Fall back to basic HTML scraping
        if not profile_data:
            print(f"Falling back to HTML scraping for {linkedin_url}")
            profile_data = extract_basic_linkedin_data_from_html(linkedin_url)
            if profile_data:
                print(f"Successfully scraped basic data for {linkedin_url}")
            else:
                print(f"Failed to scrape data for {linkedin_url}")
        
        # Create a minimal profile as last resort
        if not profile_data:
            username = linkedin_url.split("/in/")[1].split("/")[0] if "/in/" in linkedin_url else "unknown"
            profile_name = username.replace("-", " ").title()
            
            profile_data = {
                "linkedin_url": linkedin_url,
                "name": profile_name,
                "headline": "Professional",
                "location": "",
                "summary": "",
                "experience": [{"title": "Professional", "company": "Unknown"}],  # Add minimal experience
                "education": [],
                "skills": ["Professional"]  # Add minimal skills
            }
            print(f"Created minimal profile for {linkedin_url}")
        
        # Ensure the profile has at least some minimal data
        if not profile_data.get("experience"):
            profile_data["experience"] = [{"title": "Professional", "company": "Unknown"}]
        
        if not profile_data.get("skills"):
            profile_data["skills"] = ["Professional"]
        
        return profile_data
    def _get_profile_from_rapidapi(self, linkedin_url):
        """Get LinkedIn profile data using the Fresh LinkedIn Profile Data API."""
        if not RAPIDAPI_KEY:
            print("No RapidAPI key provided")
            return None
        
        # UPDATED: Use the correct endpoint as of 2025-06-28
        api_url = "https://fresh-linkedin-profile-data.p.rapidapi.com/get-linkedin-profile"
        
        querystring = {"linkedin_url": linkedin_url}
        
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "fresh-linkedin-profile-data.p.rapidapi.com"
        }
        
        try:
            print(f"Making RapidAPI request for {linkedin_url}")
            response = requests.get(api_url, headers=headers, params=querystring)
            
            if response.status_code == 200:
                data = response.json()
                return self._format_profile_data(data, linkedin_url)
            else:
                print(f"RapidAPI request failed: Status code {response.status_code}")
                if response.text:
                    print(f"Response text: {response.text[:200]}...")
                return None
        except Exception as e:
            print(f"RapidAPI request error: {e}")
            return None
    
    def _format_profile_data(self, api_data, linkedin_url, raw_data=None):
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
            
            # Parse the response data
            if isinstance(api_data, dict):
                # Try to parse data based on the response structure
                
                # First check if this is the 2025 API format with data field
                if "data" in api_data and isinstance(api_data["data"], dict):
                    data = api_data["data"]
                    
                    # Basic profile info
                    profile["name"] = data.get("full_name", "")
                    profile["headline"] = data.get("headline", "")
                    
                    # Location
                    if "location" in data and isinstance(data["location"], dict):
                        city = data["location"].get("city", "")
                        country = data["location"].get("country", "")
                        profile["location"] = f"{city}, {country}".strip(", ")
                    
                    profile["summary"] = data.get("summary", "")
                    
                    # Experience
                    if "experience" in data and isinstance(data["experience"], list):
                        for exp in data["experience"]:
                            if isinstance(exp, dict):
                                experience = {
                                    "title": exp.get("title", ""),
                                    "company": exp.get("company", ""),
                                    "duration": exp.get("duration", ""),
                                    "description": exp.get("description", "")
                                }
                                profile["experience"].append(experience)
                    
                    # Education
                    if "education" in data and isinstance(data["education"], list):
                        for edu in data["education"]:
                            if isinstance(edu, dict):
                                education = {
                                    "school": edu.get("school", ""),
                                    "degree": edu.get("degree", ""),
                                    "field": edu.get("field", ""),
                                    "dates": f"{edu.get('start_date', '')} - {edu.get('end_date', '')}"
                                }
                                profile["education"].append(education)
                    
                    # Skills
                    if "skills" in data:
                        if isinstance(data["skills"], list):
                            skills_list = data["skills"]
                            if skills_list and isinstance(skills_list[0], dict):
                                profile["skills"] = [s.get("name", "") for s in skills_list if isinstance(s, dict) and "name" in s]
                            elif skills_list and isinstance(skills_list[0], str):
                                profile["skills"] = skills_list
                
                # Alternative format with profile field
                elif "profile" in api_data and isinstance(api_data["profile"], dict):
                    profile_data = api_data["profile"]
                    
                    # Basic profile info
                    first_name = profile_data.get("firstName", "")
                    last_name = profile_data.get("lastName", "")
                    profile["name"] = f"{first_name} {last_name}".strip()
                    
                    profile["headline"] = profile_data.get("headline", "")
                    profile["location"] = profile_data.get("locationName", "")
                    profile["summary"] = profile_data.get("summary", "")
                    
                    # Experience
                    if "experience" in profile_data and isinstance(profile_data["experience"], list):
                        for exp in profile_data["experience"]:
                            if isinstance(exp, dict):
                                experience = {
                                    "title": exp.get("title", ""),
                                    "company": exp.get("companyName", ""),
                                    "duration": exp.get("dateRange", ""),
                                    "description": exp.get("description", "")
                                }
                                profile["experience"].append(experience)
                    
                    # Education
                    if "education" in profile_data and isinstance(profile_data["education"], list):
                        for edu in profile_data["education"]:
                            if isinstance(edu, dict):
                                education = {
                                    "school": edu.get("schoolName", ""),
                                    "degree": edu.get("degree", ""),
                                    "field": edu.get("fieldOfStudy", ""),
                                    "dates": edu.get("dateRange", "")
                                }
                                profile["education"].append(education)
                    
                    # Skills
                    if "skills" in profile_data and isinstance(profile_data["skills"], list):
                        skills_list = profile_data["skills"]
                        if skills_list and isinstance(skills_list[0], dict):
                            profile["skills"] = [s.get("name", "") for s in skills_list]
                        elif skills_list and isinstance(skills_list[0], str):
                            profile["skills"] = skills_list
            
            # Store raw data if provided
            if raw_data:
                profile["raw_data"] = raw_data
            
            return profile
            
        except Exception as e:
            print(f"Error formatting profile data: {e}")
            # Return a basic profile if parsing fails
            return {
                "linkedin_url": linkedin_url,
                "name": linkedin_url.split("/in/")[1].split("/")[0].replace("-", " ").title(),
                "headline": "Professional",
                "location": "",
                "experience": [],
                "education": [],
                "skills": []
            }
    
    def score_candidates(self, candidates, job_description):
        """Score candidates based on the job description."""
        print(f"Scoring {len(candidates)} candidates...")
        scored_candidates = []
        
        # Parse job requirements once
        job_req = parse_job_requirements(job_description)
        job_title = job_req.get("title", "").lower()
        job_skills = [skill.lower() for skill in job_req.get("skills", [])]
        job_location = job_req.get("location", "").lower()
        
        # Extract keywords from job description
        keywords = extract_keywords_from_job(job_description)
        
        for candidate in tqdm(candidates, desc="Scoring candidates"):
            score = self._score_candidate(candidate, job_description, job_title, job_skills, job_location, keywords)
            candidate["score"] = score
            scored_candidates.append(candidate)
        
        # Sort candidates by score (highest first)
        scored_candidates.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        print("Completed scoring candidates.")
        return scored_candidates
    
    def _score_candidate(self, candidate, job_description, job_title=None, job_skills=None, job_location=None, keywords=None):
        """Score a candidate based on the job description."""
        # Initialize score
        score = 0
        
        # Get job requirements if not provided
        if not job_title or not job_skills:
            job_req = parse_job_requirements(job_description)
            job_title = job_title or job_req.get("title", "").lower()
            job_skills = job_skills or [skill.lower() for skill in job_req.get("skills", [])]
            job_location = job_location or job_req.get("location", "").lower()
            
        if not keywords:
            keywords = extract_keywords_from_job(job_description)
        
        # Score headline match
        headline = str(candidate.get("headline", "")).lower()
        if job_title in headline:
            score += 2
        
        # Score skills match
        candidate_skills = [str(skill).lower() for skill in candidate.get("skills", [])]
        skill_matches = 0
        for job_skill in job_skills:
            for candidate_skill in candidate_skills:
                if job_skill in candidate_skill or candidate_skill in job_skill:
                    skill_matches += 1
                    break
        
        score += min(5, skill_matches)  # Cap skill score at 5
        
        # Score experience match
        experience_score = 0
        for exp in candidate.get("experience", []):
            exp_title = str(exp.get("title", "")).lower()
            exp_company = str(exp.get("company", "")).lower()
            
            # Check if job title or skills appear in experience title
            if job_title in exp_title:
                experience_score += 2
            elif any(skill in exp_title for skill in job_skills):
                experience_score += 1
            
            # Check if keywords appear in experience
            if any(keyword.lower() in exp_title or keyword.lower() in exp_company for keyword in keywords):
                experience_score += 1
        
        score += min(5, experience_score)  # Cap experience score at 5
        
        # Score education match
        education_score = 0
        edu_keywords = ["phd", "master", "ms", "bs", "bachelor", "degree"]
        for edu in candidate.get("education", []):
            edu_degree = str(edu.get("degree", "")).lower()
            edu_field = str(edu.get("field", "")).lower()
            
            # Check for advanced degrees
            if "phd" in edu_degree:
                education_score += 3
            elif "master" in edu_degree or "ms" in edu_degree:
                education_score += 2
            elif "bachelor" in edu_degree or "bs" in edu_degree or "ba" in edu_degree:
                education_score += 1
            
            # Check if education field matches keywords
            if any(keyword.lower() in edu_field for keyword in keywords):
                education_score += 1
        
        score += min(3, education_score)  # Cap education score at 3
        
        # Score location match
        if job_location:
            candidate_location = str(candidate.get("location", "")).lower()
            if job_location in candidate_location:
                score += 1
        
        # Use OpenAI for advanced scoring if available
        if OPENAI_API_KEY:
            try:
                import openai
                openai.api_key = OPENAI_API_KEY
                
                # Prepare a simplified version of the candidate for the prompt
                simple_candidate = {
                    "headline": candidate.get("headline", ""),
                    "skills": candidate.get("skills", [])[:10],  # Limit to top 10 skills
                    "experience": [
                        {
                            "title": exp.get("title", ""),
                            "company": exp.get("company", "")
                        }
                        for exp in candidate.get("experience", [])[:3]  # Limit to top 3 experiences
                    ],
                    "education": [
                        {
                            "school": edu.get("school", ""),
                            "degree": edu.get("degree", "")
                        }
                        for edu in candidate.get("education", [])[:2]  # Limit to top 2 educations
                    ]
                }
                
                # Extract key details from job description
                job_summary = "\n".join(job_description.split("\n")[:10])
                
                prompt = f"""
                Rate this candidate for the following role on a scale of 1-10:
                
                Job Description:
                {job_summary}
                
                Key Skills Needed:
                {", ".join(job_skills[:10])}
                
                Candidate:
                {json.dumps(simple_candidate, indent=2)}
                
                Provide only a numeric score from 1-10.
                """
                
                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a technical recruiter evaluating candidates."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=50
                )
                
                # Try to extract a numeric score from the response
                text_response = response.choices[0].message.content.strip()
                score_match = re.search(r"(\d+(?:\.\d+)?)", text_response)
                if score_match:
                    ai_score = float(score_match.group(1))
                    # Blend rule-based and AI scores
                    score = (score + ai_score) / 2
            except Exception as e:
                print(f"Error using OpenAI for scoring: {e}")
        
        # Cap score at 10
        return min(10, score)
    
    def generate_outreach(self, candidates, job_description):
        """Generate personalized outreach messages for candidates."""
        print(f"Generating outreach messages for {len(candidates)} candidates...")
        messages = []
        
        for candidate in candidates:
            message = self._generate_outreach_message(candidate, job_description)
            messages.append({
                "candidate": candidate.get("name", ""),
                "linkedin_url": candidate.get("linkedin_url", ""),
                "message": message
            })
        
        return messages
    
    def _generate_outreach_message(self, candidate, job_description):
        """Generate a personalized outreach message."""
        # Extract job details
        job_req = parse_job_requirements(job_description)
        job_title = job_req.get("title", "").strip()
        job_location = job_req.get("location", "").strip()
        
        # Get candidate's first name
        full_name = candidate.get("name", "")
        first_name = full_name.split(" ")[0] if full_name else "there"
        
        # Get candidate's current role or headline
        headline = candidate.get("headline", "")
        
        # Get candidate's most recent experience
        experiences = candidate.get("experience", [])
        recent_exp = experiences[0] if experiences else {"title": "your role", "company": "your company"}
        
        # Extract salary if available
        salary_range = ""
        salary_match = re.search(r"salary:?\s*\$?([\d,]+)[-\s]*[kK]?[-\s]*\$?([\d,]+)[kK]?", job_description, re.IGNORECASE)
        if salary_match:
            salary_range = f"${salary_match.group(1)}-{salary_match.group(2)}k"
        
        # Use OpenAI for personalized message if available
        if OPENAI_API_KEY:
            try:
                import openai
                openai.api_key = OPENAI_API_KEY
                
                # Prepare a simplified version of the candidate for the prompt
                simple_candidate = {
                    "name": first_name,
                    "headline": headline,
                    "experience": [
                        {
                            "title": exp.get("title", ""),
                            "company": exp.get("company", ""),
                            "duration": exp.get("duration", "")
                        }
                        for exp in experiences[:2]  # Limit to top 2 experiences
                    ],
                    "education": [
                        {
                            "school": edu.get("school", ""),
                            "degree": edu.get("degree", "")
                        }
                        for edu in candidate.get("education", [])[:1]  # Limit to top education
                    ],
                    "skills": candidate.get("skills", [])[:5]  # Limit to top 5 skills
                }
                
                # Extract key details for the message
                job_summary = "\n".join([line for line in job_description.split("\n") 
                                        if line.strip() and not line.lower().startswith("requirement")])[:500]
                
                prompt = f"""
                Create a personalized LinkedIn outreach message for this candidate:
                
                Job Summary:
                {job_summary}
                
                Job Title: {job_title}
                Location: {job_location}
                {f"Salary: {salary_range}" if salary_range else ""}
                
                Candidate:
                {json.dumps(simple_candidate, indent=2)}
                
                Requirements:
                1. Use their first name
                2. Keep the message under 150 words
                3. Mention something specific from their background that relates to the job
                4. Be friendly and professional
                5. Ask for a 15-minute chat about the opportunity
                6. Sign as "[Recruiter Name]"
                7. Don't use generic phrases like "I hope this message finds you well"
                """
                
                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a technical recruiter writing personalized outreach messages."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=300
                )
                
                ai_message = response.choices[0].message.content.strip()
                if ai_message:
                    return ai_message
            except Exception as e:
                print(f"Error using OpenAI for message generation: {e}")
        
        # Template message as fallback
        message = f"""
Hi {first_name},

I came across your profile and was impressed by your background as {headline}.

I'm reaching out because we're looking for a {job_title} to join our team. Based on your experience as {recent_exp.get('title', 'a professional')} at {recent_exp.get('company', 'your company')}, I believe you could be a great fit for this role.

{f'Were offering {salary_range} + equity for this role in {job_location}.' if salary_range and job_location else ''}

Would you be open to a 15-minute chat to discuss this opportunity further?

Best regards,
[Recruiter Name]
        """
        
        return message.strip()