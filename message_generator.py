import os
import openai
from config import OPENAI_API_KEY

class MessageGenerator:
    def __init__(self, api_key=None):
        """Initialize the message generator with OpenAI API key."""
        self.api_key = api_key or OPENAI_API_KEY
        if self.api_key:
            openai.api_key = self.api_key
    
    def generate_outreach(self, candidate, job_description, company_name="Windsurf"):
        """Generate a personalized outreach message for a candidate."""
        if not self.api_key:
            return self._generate_template_message(candidate, job_description, company_name)
        
        try:
            # Extract candidate information
            name = candidate.get('name', 'there')
            headline = candidate.get('headline', '')
            score_breakdown = candidate.get('score_breakdown', {})
            
            # Find the candidate's strengths based on score breakdown
            strengths = []
            for category, score in score_breakdown.items():
                if score >= 8:
                    strengths.append(category)
            
            # Format the prompt for OpenAI
            prompt = f"""
            Write a personalized LinkedIn outreach message to a candidate named {name} for a Software Engineer, ML Research position at {company_name}.
            
            About the candidate:
            - Current role: {headline}
            - Strengths: {', '.join(strengths) if strengths else 'Unknown'}
            
            Job Description Summary:
            {job_description[:500]}...
            
            Guidelines:
            1. Keep the message under 150 words
            2. Be authentic and personal, mentioning specific details about their profile
            3. Mention why they might be a good fit for the role
            4. Include a clear call to action
            5. Be warm and professional in tone
            6. Don't be overly formal or use generic recruiter language
            7. Don't include placeholders or variables in brackets
            
            Message:
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a skilled technical recruiter who writes personalized outreach messages."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            message = response.choices[0].message.content.strip()
            return message
            
        except Exception as e:
            print(f"Error generating message with OpenAI: {e}")
            return self._generate_template_message(candidate, job_description, company_name)
    
    def _generate_template_message(self, candidate, job_description, company_name):
        """Generate a template message when API is not available."""
        name = candidate.get('name', 'there')
        headline = candidate.get('headline', 'professional')
        
        message = f"""
        Hi {name},
        
        I came across your profile and was impressed by your experience as {headline}. We're looking for a Software Engineer with ML Research experience to join our team at {company_name}, and your background seems like it could be a great fit.
        
        We're building AI-powered developer tools that help engineers code faster and more efficiently. Given your skills, I'd love to chat about how you might contribute to our mission.
        
        Would you be open to a quick call to discuss this opportunity?
        
        Best regards,
        Recruiter @ {company_name}
        """
        
        return message.strip()
    
    def generate_batch_outreach(self, candidates, job_description, company_name="Windsurf"):
        """Generate outreach messages for multiple candidates."""
        messages = []
        
        for candidate in candidates:
            message = self.generate_outreach(candidate, job_description, company_name)
            messages.append({
                "candidate": candidate.get('name', 'Unknown'),
                "linkedin_url": candidate.get('linkedin_url', ''),
                "message": message
            })
        
        return messages