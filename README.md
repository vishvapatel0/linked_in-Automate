# LinkedIn Agent

A powerful, automated tool for sourcing candidates from LinkedIn based on job descriptions. This agent intelligently searches for relevant profiles, extracts comprehensive candidate data, scores potential matches, and generates personalized outreach messages—all without manual intervention.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [Workflow](#workflow)
- [API Integrations](#api-integrations)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [Future Enhancements](#future-enhancements)
- [Disclaimer](#disclaimer)

## 🔍 Overview

The LinkedIn Sourcing Agent streamlines the recruitment process by automating the discovery and initial assessment of potential candidates. It analyzes job descriptions to understand requirements, searches for matching LinkedIn profiles, gathers detailed information about candidates, evaluates their suitability, and prepares personalized outreach messages—significantly reducing the time and effort required for talent sourcing.

## ✨ Features

- **Smart Job Analysis**: Extracts key requirements, skills, and keywords from job descriptions
- **Multi-Source Search**: Leverages both Serper API and Google search to find relevant profiles
- **Comprehensive Profile Data**: Retrieves detailed information using LinkedIn Profile Data API
- **Intelligent Filtering**: Ensures only relevant candidates are considered
- **Advanced Scoring Algorithm**: Evaluates candidates based on skills, experience, education, and location
- **Personalized Outreach**: Generates customized messages tailored to each candidate's background
- **Detailed Reporting**: Saves comprehensive results for further analysis

## 🛠️ Requirements

- Python 3.8 or higher
- RapidAPI Key for Fresh LinkedIn Profile Data API
- Serper API Key (optional but recommended for better search results)
- OpenAI API Key (optional, for enhanced scoring and message generation)

## 📦 Installation

1. Clone the repository:
```bash
git clone https://github.com/DarkSchneider544/linkedin-sourcing-agent.git
cd linkedin-sourcing-agent
Install required packages:
bash
pip install -r requirements.txt
Create a .env file in the project root with your API keys:
Code
RAPIDAPI_KEY=your_rapidapi_key_here
SERP_API_KEY=your_serper_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
📁 Project Structure
Code
linkedin-sourcing-agent/
├── main.py                 # Main entry point
├── linkedin_agent.py       # Core agent implementation
├── utils.py                # Utility functions
├── data_store.py           # Data storage functionality
├── job_samples.py          # Sample job descriptions
├── requirements.txt        # Project dependencies
├── data/                   # Directory for storing results
└── README.md               # Project documentation
🚀 Usage
Basic Usage
Run the agent with default settings:

bash
python main.py --max 5 --top 2 --output results.json
Using a Custom Job Description
bash
python main.py --job-file path/to/job_description.txt --output results.json
Advanced Options
bash
python main.py --max 10 --top 3 --output results.json --verbose
Command-Line Parameters
Parameter	Description	Default
--max	Maximum number of candidates to retrieve	5
--top	Number of top candidates to generate outreach for	2
--output	Output JSON file name	results.json
--job-file	Path to file containing job description	(uses default)
--rapidapi	Use RapidAPI for profile data	True
--serper	Use Serper API for searches	True
--verbose	Display detailed candidate information	False
🔄 Workflow
Job Analysis

Parse the job description to extract title, skills, requirements, and keywords
Build optimized search queries based on these requirements
Profile Search

Execute searches using Serper API and/or Google search
Extract LinkedIn profile URLs from search results
Filter URLs to remove duplicates
Profile Data Extraction

Retrieve detailed profile data using RapidAPI
Extract info like experience, education, skills, and location
Apply fallback mechanisms if API calls fail
Candidate Filtering

Filter candidates based on relevance to job requirements
Ensure only qualified candidates are considered
Candidate Scoring

Score candidates based on multiple factors:
Skills match
Experience relevance
Education qualifications
Location match
Outreach Generation

Create personalized outreach messages for top candidates
Include specific details from their profile and the job description
Results Storage

Save detailed results to JSON file
Include all candidate profiles and generated messages
🔌 API Integrations
RapidAPI - Fresh LinkedIn Profile Data
Used to extract detailed profile information from LinkedIn URLs.

Python
def _get_profile_from_rapidapi(self, linkedin_url):
    """Get LinkedIn profile data using the Fresh LinkedIn Profile Data API."""
    if not RAPIDAPI_KEY:
        print("No RapidAPI key provided")
        return None
    
    api_url = "https://fresh-linkedin-profile-data.p.rapidapi.com/get-linkedin-profile"
    
    querystring = {"linkedin_url": linkedin_url}
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "fresh-linkedin-profile-data.p.rapidapi.com"
    }
    
    try:
        response = requests.get(api_url, headers=headers, params=querystring)
        
        if response.status_code == 200:
            data = response.json()
            return self._format_profile_data(data, linkedin_url)
        else:
            print(f"RapidAPI request failed: Status code {response.status_code}")
            return None
    except Exception as e:
        print(f"RapidAPI request error: {e}")
        return None
Serper API
Used for high-quality search results to find LinkedIn profiles.

Python
def extract_linkedin_urls_from_serp(search_query, num_results=10):
    """Use Serper API to find LinkedIn profiles."""
    if not SERP_API_KEY:
        print("No Serper API key provided")
        return []
    
    url = "https://google.serper.dev/search"
    
    payload = json.dumps({
        "q": f"site:linkedin.com/in/ {search_query}",
        "num": num_results
    })
    
    headers = {
        'X-API-KEY': SERP_API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, data=payload)
        
        if response.status_code == 200:
            data = response.json()
            
            linkedin_urls = []
            
            # Process organic results
            if "organic" in data:
                for result in data["organic"]:
                    link = result.get("link", "")
                    if "linkedin.com/in/" in link:
                        clean_url = link.split('?')[0]  # Remove query parameters
                        linkedin_urls.append(clean_url)
            
            return linkedin_urls[:num_results]
        else:
            print(f"Serper API request failed: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error using Serper API: {e}")
        return []
❗ Troubleshooting
Common Issues
No Candidates Found

Problem: The agent returns zero candidates.
Solutions:
Check that your API keys are valid and properly configured in .env
Ensure your job description contains clear skills and requirements
Try using a more general job title or fewer specific requirements
Run with --verbose flag to see detailed debugging information
Poor Quality Candidates

Problem: The candidates don't match the job requirements well.
Solutions:
Improve the job description with more specific requirements
Adjust the scoring thresholds in _score_candidate method
Add more relevant skills and keywords to the job description
API Rate Limiting

Problem: You hit API rate limits during execution.
Solutions:
Reduce the --max parameter value
Implement a delay between API calls
Use a premium API plan with higher limits
Slow Performance

Problem: The agent takes too long to complete.
Solutions:
Use Serper API instead of Google search (--serper flag)
Reduce the number of candidates to process
Cache results for reuse in future runs
💡 Best Practices
Job Descriptions: Provide detailed and specific job descriptions for better results.
API Keys: Keep your API keys secure in the .env file and never commit them to version control.
Rate Limits: Be mindful of API rate limits, especially for the LinkedIn Profile Data API.
Customization: The scoring algorithm can be customized in the _score_candidate method to match your specific requirements.
Data Storage: Regularly clean up the data directory to manage disk space.
Testing: Start with a small number of candidates to test before running larger searches.
🔮 Future Enhancements
Implement parallel processing for faster profile extraction
Add support for multiple job descriptions in a single run
Develop a web interface for easier interaction
Incorporate machine learning for better candidate matching
Add integration with email systems for automated outreach
Support for other professional networks beyond LinkedIn
Implementation of A/B testing for outreach messages
⚠️ Disclaimer
This tool is for educational and research purposes only. Users are responsible for ensuring compliance with LinkedIn's terms of service, privacy policies, and all applicable laws regarding data usage and privacy. Always obtain proper consent before contacting individuals and respect their privacy preferences.

Developed by DarkSchneider544
Last Updated: June 28, 2025

Code

This README.md file is now ready to be uploaded directly to your GitHub repository. It's professionally formatted with emoji icons, clear sections, code examples, and detailed explanations of your LinkedIn Sourcing Agent project.

To upload it:

1. Go to your GitHub repository (create one if you don't have it yet)
2. Click "Add file" > "Create new file"
3. Name it "README.md"
4. Paste the entire content above into the editor
5. Click "Commit new file"

Your repository will immediately display this professional README on its main page.
You said: i want markdown of complete text
i want markdown of complete text 
Copilot said: Here's the complete markdown text for your
Here's the complete markdown text for your LinkedIn Sourcing Agent README:

Markdown
# LinkedIn Sourcing Agent

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-brightgreen)
![Last Updated](https://img.shields.io/badge/last%20updated-June%202025-orange)

A powerful, automated tool for sourcing candidates from LinkedIn based on job descriptions. This agent intelligently searches for relevant profiles, extracts comprehensive candidate data, scores potential matches, and generates personalized outreach messages—all without manual intervention.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [Workflow](#workflow)
- [API Integrations](#api-integrations)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [Future Enhancements](#future-enhancements)
- [Disclaimer](#disclaimer)

## 🔍 Overview

The LinkedIn Sourcing Agent streamlines the recruitment process by automating the discovery and initial assessment of potential candidates. It analyzes job descriptions to understand requirements, searches for matching LinkedIn profiles, gathers detailed information about candidates, evaluates their suitability, and prepares personalized outreach messages—significantly reducing the time and effort required for talent sourcing.

## ✨ Features

- **Smart Job Analysis**: Extracts key requirements, skills, and keywords from job descriptions
- **Multi-Source Search**: Leverages both Serper API and Google search to find relevant profiles
- **Comprehensive Profile Data**: Retrieves detailed information using LinkedIn Profile Data API
- **Intelligent Filtering**: Ensures only relevant candidates are considered
- **Advanced Scoring Algorithm**: Evaluates candidates based on skills, experience, education, and location
- **Personalized Outreach**: Generates customized messages tailored to each candidate's background
- **Detailed Reporting**: Saves comprehensive results for further analysis

## 🛠️ Requirements

- Python 3.8 or higher
- RapidAPI Key for Fresh LinkedIn Profile Data API
- Serper API Key (optional but recommended for better search results)
- OpenAI API Key (optional, for enhanced scoring and message generation)

## 📦 Installation

1. Clone the repository:
```bash
git clone https://github.com/DarkSchneider544/linkedin-sourcing-agent.git
cd linkedin-sourcing-agent
Install required packages:
bash
pip install -r requirements.txt
Create a .env file in the project root with your API keys:
Code
RAPIDAPI_KEY=your_rapidapi_key_here
SERP_API_KEY=your_serper_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
📁 Project Structure
Code
linkedin-sourcing-agent/
├── main.py                 # Main entry point
├── linkedin_agent.py       # Core agent implementation
├── utils.py                # Utility functions
├── data_store.py           # Data storage functionality
├── job_samples.py          # Sample job descriptions
├── requirements.txt        # Project dependencies
├── data/                   # Directory for storing results
└── README.md               # Project documentation
🚀 Usage
Basic Usage
Run the agent with default settings:

bash
python main.py --max 5 --top 2 --output results.json
Using a Custom Job Description
bash
python main.py --job-file path/to/job_description.txt --output results.json
Advanced Options
bash
python main.py --max 10 --top 3 --output results.json --verbose
Command-Line Parameters
Parameter	Description	Default
--max	Maximum number of candidates to retrieve	5
--top	Number of top candidates to generate outreach for	2
--output	Output JSON file name	results.json
--job-file	Path to file containing job description	(uses default)
--rapidapi	Use RapidAPI for profile data	True
--serper	Use Serper API for searches	True
--verbose	Display detailed candidate information	False
🔄 Workflow
Job Analysis

Parse the job description to extract title, skills, requirements, and keywords
Build optimized search queries based on these requirements
Profile Search

Execute searches using Serper API and/or Google search
Extract LinkedIn profile URLs from search results
Filter URLs to remove duplicates
Profile Data Extraction

Retrieve detailed profile data using RapidAPI
Extract info like experience, education, skills, and location
Apply fallback mechanisms if API calls fail
Candidate Filtering

Filter candidates based on relevance to job requirements
Ensure only qualified candidates are considered
Candidate Scoring

Score candidates based on multiple factors:
Skills match
Experience relevance
Education qualifications
Location match
Outreach Generation

Create personalized outreach messages for top candidates
Include specific details from their profile and the job description
Results Storage

Save detailed results to JSON file
Include all candidate profiles and generated messages
🔌 API Integrations
RapidAPI - Fresh LinkedIn Profile Data
Used to extract detailed profile information from LinkedIn URLs.

Python
def _get_profile_from_rapidapi(self, linkedin_url):
    """Get LinkedIn profile data using the Fresh LinkedIn Profile Data API."""
    if not RAPIDAPI_KEY:
        print("No RapidAPI key provided")
        return None
    
    api_url = "https://fresh-linkedin-profile-data.p.rapidapi.com/get-linkedin-profile"
    
    querystring = {"linkedin_url": linkedin_url}
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "fresh-linkedin-profile-data.p.rapidapi.com"
    }
    
    try:
        response = requests.get(api_url, headers=headers, params=querystring)
        
        if response.status_code == 200:
            data = response.json()
            return self._format_profile_data(data, linkedin_url)
        else:
            print(f"RapidAPI request failed: Status code {response.status_code}")
            return None
    except Exception as e:
        print(f"RapidAPI request error: {e}")
        return None
Serper API
Used for high-quality search results to find LinkedIn profiles.

Python
def extract_linkedin_urls_from_serp(search_query, num_results=10):
    """Use Serper API to find LinkedIn profiles."""
    if not SERP_API_KEY:
        print("No Serper API key provided")
        return []
    
    url = "https://google.serper.dev/search"
    
    payload = json.dumps({
        "q": f"site:linkedin.com/in/ {search_query}",
        "num": num_results
    })
    
    headers = {
        'X-API-KEY': SERP_API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, data=payload)
        
        if response.status_code == 200:
            data = response.json()
            
            linkedin_urls = []
            
            # Process organic results
            if "organic" in data:
                for result in data["organic"]:
                    link = result.get("link", "")
                    if "linkedin.com/in/" in link:
                        clean_url = link.split('?')[0]  # Remove query parameters
                        linkedin_urls.append(clean_url)
            
            return linkedin_urls[:num_results]
        else:
            print(f"Serper API request failed: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error using Serper API: {e}")
        return []
❗ Troubleshooting
Common Issues
No Candidates Found

Problem: The agent returns zero candidates.
Solutions:
Check that your API keys are valid and properly configured in .env
Ensure your job description contains clear skills and requirements
Try using a more general job title or fewer specific requirements
Run with --verbose flag to see detailed debugging information
Poor Quality Candidates

Problem: The candidates don't match the job requirements well.
Solutions:
Improve the job description with more specific requirements
Adjust the scoring thresholds in _score_candidate method
Add more relevant skills and keywords to the job description
API Rate Limiting

Problem: You hit API rate limits during execution.
Solutions:
Reduce the --max parameter value
Implement a delay between API calls
Use a premium API plan with higher limits
Slow Performance

Problem: The agent takes too long to complete.
Solutions:
Use Serper API instead of Google search (--serper flag)
Reduce the number of candidates to process
Cache results for reuse in future runs
💡 Best Practices
Job Descriptions: Provide detailed and specific job descriptions for better results.
API Keys: Keep your API keys secure in the .env file and never commit them to version control.
Rate Limits: Be mindful of API rate limits, especially for the LinkedIn Profile Data API.
Customization: The scoring algorithm can be customized in the _score_candidate method to match your specific requirements.
Data Storage: Regularly clean up the data directory to manage disk space.
Testing: Start with a small number of candidates to test before running larger searches.
🔮 Future Enhancements
Implement parallel processing for faster profile extraction
Add support for multiple job descriptions in a single run
Develop a web interface for easier interaction
Incorporate machine learning for better candidate matching
Add integration with email systems for automated outreach
Support for other professional networks beyond LinkedIn
Implementation of A/B testing for outreach messages
⚠️ Disclaimer
This tool is for educational and research purposes only. Users are responsible for ensuring compliance with LinkedIn's terms of service, privacy policies, and all applicable laws regarding data usage and privacy. Always obtain proper consent before contacting individuals and respect their privacy preferences.

Developed by DarkSchneider544
Last Updated: June 28, 2025

Code

You can now copy this entire markdown text and use it directly for your GitHub repositor
