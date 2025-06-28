import re
from datetime import datetime
from config import (
    SCORING_WEIGHTS, TOP_ML_COMPANIES, TOP_UNIVERSITIES, 
    ML_AI_SKILLS, TARGET_LOCATION, NEARBY_LOCATIONS
)
from utils import calculate_weighted_average

class CandidateScorer:
    def __init__(self, job_description):
        self.job_description = job_description
        self.job_requirements = self._parse_job_requirements()
        
    def _parse_job_requirements(self):
        """Extract key requirements from the job description."""
        # Extract skills, education, experience, location
        from utils import parse_job_requirements
        return parse_job_requirements(self.job_description)
        
    def score_candidate(self, candidate_data):
        """Score a candidate based on the scoring rubric."""
        if not candidate_data:
            return {"total": 0, "breakdown": {}}
            
        # Calculate individual category scores
        education_score = self._score_education(candidate_data)
        career_score = self._score_career_trajectory(candidate_data)
        company_score = self._score_company_relevance(candidate_data)
        experience_score = self._score_experience_match(candidate_data)
        location_score = self._score_location_match(candidate_data)
        tenure_score = self._score_tenure(candidate_data)
        
        # Compile score breakdown
        score_breakdown = {
            "education": education_score,
            "career_trajectory": career_score,
            "company_relevance": company_score,
            "experience_match": experience_score,
            "location_match": location_score,
            "tenure": tenure_score
        }
        
        # Calculate weighted score
        total_score = calculate_weighted_average(score_breakdown, SCORING_WEIGHTS)
        
        return {
            "total": total_score,
            "breakdown": score_breakdown
        }
    
    def _score_education(self, candidate):
        """Score education (20%)
        - Elite schools (MIT, Stanford, etc.): 9-10
        - Strong schools: 7-8
        - Standard universities: 5-6
        - Clear progression: 8-10
        """
        score = 5  # Default score
        
        # Check for education information
        education = candidate.get('education', [])
        if not education and isinstance(candidate.get('raw_data'), dict):
            education = candidate.get('raw_data', {}).get('education', [])
        
        if not education:
            return score
            
        highest_degree_score = 0
        progression_score = 0
        school_score = 0
        
        # Check degree level
        degree_scores = {
            'phd': 10, 'doctorate': 10, 'ph.d': 10,
            'master': 8, 'ms': 8, 'msc': 8, 'ma': 8,
            'bachelor': 6, 'bs': 6, 'bsc': 6, 'ba': 6
        }
        
        # Check for elite schools
        for edu in education:
            # School name could be in different fields depending on the data structure
            school_name = None
            if isinstance(edu, dict):
                school_name = edu.get('school') or edu.get('schoolName') or edu.get('institution')
            elif isinstance(edu, str):
                school_name = edu
                
            if not school_name:
                continue
                
            # Check if this is a top university
            for top_school in TOP_UNIVERSITIES:
                if top_school.lower() in school_name.lower():
                    school_score = max(school_score, 10)  # Elite school
                    break
            
            # If not found in top universities, give a default score
            if school_score < 5:
                school_score = 6  # Standard university
                
            # Check degree level
            degree_field = None
            if isinstance(edu, dict):
                degree_field = edu.get('degree') or edu.get('degreeName') or ''
            elif isinstance(edu, str):
                degree_field = edu
                
            for degree_key, degree_value in degree_scores.items():
                if degree_field and degree_key in degree_field.lower():
                    highest_degree_score = max(highest_degree_score, degree_value)
                    break
        
        # Check for clear progression
        if len(education) > 1:
            progression_score = 8  # Multiple degrees suggest progression
            
        # Combine the scores
        score = max(highest_degree_score, school_score, progression_score)
        
        return min(10, score)  # Cap at 10
    
    def _score_career_trajectory(self, candidate):
        """Score career trajectory (20%)
        - Steady growth: 6-8
        - Limited progression: 3-5
        """
        score = 5  # Default score
        
        # Check for experience information
        experience = candidate.get('experience', [])
        if not experience and isinstance(candidate.get('raw_data'), dict):
            experience = candidate.get('raw_data', {}).get('experience', [])
        
        if not experience or len(experience) == 0:
            return score
            
        # Sort experiences by date if possible
        sorted_experience = []
        try:
            for exp in experience:
                if isinstance(exp, dict):
                    # Extract title and company
                    title = exp.get('title', '') or exp.get('jobTitle', '')
                    company = exp.get('company', '') or exp.get('companyName', '')
                    
                    # Try to extract start and end dates
                    start_date = None
                    end_date = None
                    
                    if 'dates' in exp:
                        date_range = exp['dates']
                        if isinstance(date_range, str):
                            dates = date_range.split(' - ')
                            if len(dates) >= 2:
                                start_date = dates[0]
                                end_date = dates[1] if dates[1] != 'Present' else datetime.now().strftime('%Y-%m')
                    
                    # Add to sorted experience
                    sorted_experience.append({
                        'title': title,
                        'company': company,
                        'start_date': start_date,
                        'end_date': end_date
                    })
            
            # Sort by start date if available
            if len(sorted_experience) > 0 and sorted_experience[0]['start_date']:
                sorted_experience.sort(key=lambda x: x['start_date'])
        except:
            # If sorting fails, just use the original experience list
            sorted_experience = experience
        
        # Check for promotion patterns or title changes indicating growth
        previous_title = None
        growth_indicators = 0
        
        for exp in sorted_experience:
            current_title = ''
            if isinstance(exp, dict):
                current_title = exp.get('title', '') or exp.get('jobTitle', '')
            
            # Check for promotion indicators
            if previous_title and current_title:
                # Look for senior/lead/manager/director/vp in newer roles
                promotion_indicators = ['senior', 'lead', 'manager', 'director', 'vp', 'head', 'chief']
                for indicator in promotion_indicators:
                    if indicator in current_title.lower() and indicator not in previous_title.lower():
                        growth_indicators += 1
            
            previous_title = current_title
        
        # Score based on career growth
        if growth_indicators >= 2:
            score = 8  # Strong career growth
        elif growth_indicators == 1:
            score = 7  # Moderate career growth
        elif len(sorted_experience) >= 3:
            score = 6  # At least has multiple experiences
        else:
            score = 5  # Limited evidence of career progression
        
        return min(10, score)  # Cap at 10
    
    def _score_company_relevance(self, candidate):
        """Score company relevance (15%)
        - Top tech companies: 9-10
        - Relevant industry: 7-8
        - Any experience: 5-6
        """
        score = 5  # Default score
        
        # Check for experience information
        experience = candidate.get('experience', [])
        if not experience and isinstance(candidate.get('raw_data'), dict):
            experience = candidate.get('raw_data', {}).get('experience', [])
        
        if not experience:
            return score
            
        highest_company_score = 0
        
        for exp in experience:
            company_name = None
            if isinstance(exp, dict):
                company_name = exp.get('company', '') or exp.get('companyName', '')
            elif isinstance(exp, str) and 'at' in exp:
                # Try to extract company name from strings like "Software Engineer at Google"
                company_name = exp.split('at')[-1].strip()
            
            if not company_name:
                continue
                
            # Check if this is a top ML/AI company
            for top_company in TOP_ML_COMPANIES:
                if top_company.lower() in company_name.lower():
                    highest_company_score = max(highest_company_score, 10)  # Top tech company
                    break
            
            # Check for relevant industry keywords
            relevant_keywords = [
                'ai', 'ml', 'machine learning', 'artificial intelligence',
                'tech', 'software', 'data', 'research', 'nlp', 'computer vision'
            ]
            
            for keyword in relevant_keywords:
                if keyword in company_name.lower():
                    highest_company_score = max(highest_company_score, 8)  # Relevant industry
        
        # If we found any relevant company experience, use that score
        if highest_company_score > 0:
            score = highest_company_score
        elif len(experience) > 0:
            score = 5  # At least has some experience
        
        return min(10, score)  # Cap at 10
    
    def _score_experience_match(self, candidate):
        """Score experience match (25%)
        - Perfect skill match: 9-10
        - Strong overlap: 7-8
        - Some relevant skills: 5-6
        """
        score = 5  # Default score
        
        # Get candidate skills
        skills = candidate.get('skills', [])
        if not skills and isinstance(candidate.get('raw_data'), dict):
            skills = candidate.get('raw_data', {}).get('skills', [])
        
        # Also check experience and headline for skills
        experience_text = ""
        if 'experience' in candidate:
            for exp in candidate['experience']:
                if isinstance(exp, dict):
                    experience_text += exp.get('title', '') + " "
                    experience_text += exp.get('description', '') + " "
                elif isinstance(exp, str):
                    experience_text += exp + " "
        
        headline = candidate.get('headline', '')
        
        # If we don't have explicit skills, try to extract from headline and experience
        if not skills:
            # Create a list of skills from headline and experience
            skills = []
            for skill in ML_AI_SKILLS:
                if skill.lower() in headline.lower() or skill.lower() in experience_text.lower():
                    skills.append(skill)
        
        # Convert skills to a list of strings if it's not already
        skill_list = []
        for skill in skills:
            if isinstance(skill, dict):
                skill_name = skill.get('name', '') or skill.get('skillName', '')
                if skill_name:
                    skill_list.append(skill_name)
            elif isinstance(skill, str):
                skill_list.append(skill)
        
        # Count the number of required skills the candidate has
        required_skills = self.job_requirements.get('required_skills', [])
        matching_skills = 0
        
        for req_skill in required_skills:
            for candidate_skill in skill_list:
                if req_skill.lower() in candidate_skill.lower() or candidate_skill.lower() in req_skill.lower():
                    matching_skills += 1
                    break
        
        # Score based on the percentage of matching skills
        if required_skills:
            match_percentage = matching_skills / len(required_skills)
            
            if match_percentage >= 0.9:
                score = 10  # Perfect skill match
            elif match_percentage >= 0.7:
                score = 9  # Excellent skill match
            elif match_percentage >= 0.5:
                score = 8  # Strong overlap
            elif match_percentage >= 0.3:
                score = 7  # Good overlap
            elif matching_skills > 0:
                score = 6  # Some relevant skills
            else:
                score = 5  # Limited skill match
        
        # Check experience text and headline for additional ML/AI keywords
        ml_ai_keywords = [
            'machine learning', 'deep learning', 'ai', 'artificial intelligence', 
            'ml engineer', 'research', 'pytorch', 'tensorflow', 'nlp', 'llm'
        ]
        
        keyword_matches = 0
        for keyword in ml_ai_keywords:
            if keyword in headline.lower() or keyword in experience_text.lower():
                keyword_matches += 1
        
        # Boost score based on keyword matches
        if keyword_matches >= 3 and score < 8:
            score += 1
        
        return min(10, score)  # Cap at 10
    
    def _score_location_match(self, candidate):
        """Score location match (10%)
        - Exact city: 10
        - Same metro: 8
        - Remote-friendly: 6
        """
        score = 5  # Default score
        
        # Get candidate location
        location = candidate.get('location', '')
        if not location and isinstance(candidate.get('raw_data'), dict):
            location = candidate.get('raw_data', {}).get('location', '')
        
        if not location:
            # Try to extract location from headline or other fields
            headline = candidate.get('headline', '')
            if 'remote' in headline.lower():
                return 6  # Remote-friendly
            
            # Check if location might be in the headline
            for city in [TARGET_LOCATION] + NEARBY_LOCATIONS:
                if city.lower() in headline.lower():
                    location = city
                    break
        
        # If still no location, default score
        if not location:
            return score
        
        # Check for exact city match
        if TARGET_LOCATION.lower() in location.lower():
            score = 10  # Exact city match
        else:
            # Check for nearby locations
            for nearby in NEARBY_LOCATIONS:
                if nearby.lower() in location.lower():
                    score = 8  # Same metro area
                    break
            
            # Check for state/region match
            if 'ca' in location.lower() or 'california' in location.lower():
                score = max(score, 7)  # Same state
        
        # Check for remote indicators
        if 'remote' in location.lower():
            score = max(score, 6)  # Remote-friendly
        
        return min(10, score)  # Cap at 10
    
    def _score_tenure(self, candidate):
        """Score tenure (10%)
        - 2-3 years average: 9-10
        - 1-2 years: 6-8
        - Job hopping: 3-5
        """
        score = 5  # Default score
        
        # Check for experience information
        experience = candidate.get('experience', [])
        if not experience and isinstance(candidate.get('raw_data'), dict):
            experience = candidate.get('raw_data', {}).get('experience', [])
        
        if not experience:
            return score
            
        # Calculate average tenure
        total_duration = 0
        job_count = 0
        
        for exp in experience:
            if isinstance(exp, dict):
                # Try to extract duration
                duration = exp.get('duration', '')
                if not duration:
                    # Try to calculate from dates
                    start_date = None
                    end_date = None
                    
                    if 'dates' in exp:
                        date_range = exp['dates']
                        if isinstance(date_range, str):
                            dates = date_range.split(' - ')
                            if len(dates) >= 2:
                                try:
                                    # Handle date formats like "Jan 2020 - Present"
                                    start_str = dates[0]
                                    end_str = dates[1]
                                    
                                    # Convert to approximate months
                                    if 'present' in end_str.lower():
                                        end_date = datetime.now()
                                    else:
                                        # This is a simplified approach, would need more robust parsing
                                        end_parts = end_str.split()
                                        if len(end_parts) >= 2:  # Format: "Jan 2020"
                                            month_map = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
                                                      "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
                                            month = month_map.get(end_parts[0].lower()[:3], 1)
                                            year = int(end_parts[1])
                                            end_date = datetime(year, month, 1)
                                    
                                    start_parts = start_str.split()
                                    if len(start_parts) >= 2:
                                        month_map = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
                                                  "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
                                        month = month_map.get(start_parts[0].lower()[:3], 1)
                                        year = int(start_parts[1])
                                        start_date = datetime(year, month, 1)
                                    
                                    if start_date and end_date:
                                        # Calculate duration in years
                                        duration_days = (end_date - start_date).days
                                        duration_years = duration_days / 365
                                        total_duration += duration_years
                                        job_count += 1
                                except:
                                    # If parsing fails, ignore this entry
                                    pass
        
        # Calculate average tenure if we have job counts
        if job_count > 0:
            avg_tenure = total_duration / job_count
            
            if avg_tenure >= 3:
                score = 10  # Excellent tenure
            elif avg_tenure >= 2:
                score = 9  # Very good tenure
            elif avg_tenure >= 1.5:
                score = 8  # Good tenure
            elif avg_tenure >= 1:
                score = 7  # Decent tenure
            else:
                score = 5  # Short tenure / job hopping
        
        return min(10, score)  # Cap at 10