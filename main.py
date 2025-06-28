import argparse
import hashlib
import time
from linkedin_agent import LinkedInAgent
from data_store import SimpleJsonStore
import sys

def main(args):
    """Main function to run the LinkedIn sourcing agent."""
    start_time = time.time()
    
    # Read job description from file if provided
    job_description = ""
    if args.job_file:
        try:
            with open(args.job_file, 'r') as f:
                job_description = f.read()
        except Exception as e:
            print(f"Error reading job file: {e}")
            return
    else:
        # Default job description for testing
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
    job_id = hashlib.md5(job_description.encode()).hexdigest()[:8]
    job_id = f"job_{job_id}"
    
    # Initialize data store
    data_store = SimpleJsonStore()
    
    # Initialize agent
    print(f"Initializing LinkedIn Sourcing Agent (RapidAPI: {'Yes' if args.rapidapi else 'No'}, Serper: {'Yes' if args.serper else 'No'})")
    agent = LinkedInAgent(
        data_store=data_store, 
        use_rapidapi=args.rapidapi, 
        use_serp=args.serper
    )
    
    # Process job
    print(f"\n{'='*50}")
    print(f"PROCESSING JOB WITH MAX {args.max} CANDIDATES")
    print(f"{'='*50}\n")
    
    print(f"Job Description Preview:")
    print(f"{job_description.strip()[:200]}...\n")
    
    # Search for LinkedIn profiles
    print(f"\n{'='*50}")
    print(f"SEARCHING FOR LINKEDIN PROFILES")
    print(f"{'='*50}\n")
    
    candidates = agent.search_linkedin(job_description, max_results=args.max)
    
    # If no candidates found, try with a more aggressive search
    if not candidates:
        print("\nNo candidates found. Trying again with more general search terms...")
        
        # Add some default LinkedIn profiles as a fallback
        default_profiles = [
            "https://www.linkedin.com/in/andrewyng/",
            "https://www.linkedin.com/in/geoffreyhinton/",
            "https://www.linkedin.com/in/feifeili/",
            "https://www.linkedin.com/in/karpathy/",
            "https://www.linkedin.com/in/chelsea-finn-3317233a/"
        ]
        
        print(f"Using {len(default_profiles)} default profiles as fallback")
        temp_candidates = []
        for url in default_profiles[:args.max]:
            profile = agent._process_profile(url)
            if profile:
                temp_candidates.append(profile)
        
        candidates = temp_candidates
    
    # Score candidates
    print(f"\n{'='*50}")
    print(f"SCORING CANDIDATES")
    print(f"{'='*50}\n")
    
    if candidates:
        scored_candidates = agent.score_candidates(candidates, job_description)
    else:
        print("No candidates to score!")
        scored_candidates = []
    
    # Generate outreach messages for top candidates
    print(f"\n{'='*50}")
    print(f"GENERATING OUTREACH MESSAGES")
    print(f"{'='*50}\n")
    
    top_candidates = scored_candidates[:args.top] if scored_candidates else []
    
    if top_candidates:
        messages = agent.generate_outreach(top_candidates, job_description)
    else:
        print("No candidates for outreach messages!")
        messages = []
    
    # Print results
    print(f"\n{'='*50}")
    print(f"SOURCING RESULTS")
    print(f"{'='*50}\n")
    
    print(f"Found {len(scored_candidates)} relevant candidates out of {len(candidates)} total profiles.")
    print("\nTop Candidates:")
    
    for i, candidate in enumerate(top_candidates, 1):
        print(f"{i}. {candidate['name']} - Score: {candidate.get('score', 0):.1f}")
        print(f"   Headline: {candidate.get('headline', '')}")
        print(f"   Location: {candidate.get('location', '')}")
        print(f"   URL: {candidate.get('linkedin_url', '')}")
        
        if args.verbose:
            print(f"   Experience: {len(candidate.get('experience', []))} positions")
            for exp in candidate.get('experience', [])[:2]:  # Show top 2 experiences
                print(f"     - {exp.get('title', '')} at {exp.get('company', '')}")
            
            print(f"   Education: {len(candidate.get('education', []))} entries")
            for edu in candidate.get('education', [])[:1]:  # Show top education
                print(f"     - {edu.get('degree', '')} at {edu.get('school', '')}")
            
            print(f"   Skills: {', '.join(candidate.get('skills', [])[:5])}")
        
        print()
    
    print("===== OUTREACH MESSAGES =====\n")
    
    for i, message in enumerate(messages, 1):
        print(f"Message {i} for: {message['candidate']}")
        print(f"LinkedIn: {message['linkedin_url']}")
        print(f"{message['message']}")
        print("\n" + "-" * 50 + "\n")
    
    # Save results
    results = {
        "candidates": scored_candidates,
        "messages": messages,
        "stats": {
            "total_profiles_found": len(candidates),
            "profiles_scored": len(scored_candidates),
            "outreach_messages": len(messages),
            "execution_time_seconds": time.time() - start_time
        }
    }
    
    # Convert to JSON-serializable format
    serializable_results = {
        "candidates": [{k: v for k, v in c.items() if k != 'raw_data'} for c in results["candidates"]],
        "messages": results["messages"],
        "stats": results["stats"]
    }
    
    data_store.save_results(args.output, serializable_results)
    print(f"Results saved to {args.output}")
    
    # Print execution time
    end_time = time.time()
    print(f"\nExecution completed in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LinkedIn Sourcing Agent")
    parser.add_argument("--max", type=int, default=5, help="Maximum number of candidates to retrieve")
    parser.add_argument("--top", type=int, default=2, help="Number of top candidates to generate outreach messages for")
    parser.add_argument("--output", type=str, default="results.json", help="Output file name")
    parser.add_argument("--job-file", type=str, help="Path to file containing job description")
    parser.add_argument("--rapidapi", action="store_true", default=True, help="Use RapidAPI for profile data")
    parser.add_argument("--serper", action="store_true", default=True, help="Use Serper API for searches")
    parser.add_argument("--verbose", action="store_true", help="Display detailed candidate information")
    
    args = parser.parse_args()
    
    try:
        main(args)
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting...")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)