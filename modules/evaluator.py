"""
Evaluator Module
Uses LangChain and OpenAI to evaluate candidate resumes autonomously
"""
import json
import os
import logging
from typing import Dict, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Experience level configurations
EXPERIENCE_EXPECTATIONS = {
    "Fresher (0-1 years)": {
        "min_years": 0,
        "max_years": 1,
        "expectations": "basic understanding of core concepts, academic projects, internships"
    },
    "Junior (1-3 years)": {
        "min_years": 1,
        "max_years": 3,
        "expectations": "practical experience, code quality awareness, teamwork"
    },
    "Mid-Level (3-5 years)": {
        "min_years": 3,
        "max_years": 5,
        "expectations": "solid technical skills, system design basics, mentoring ability"
    },
    "Senior (5-8 years)": {
        "min_years": 5,
        "max_years": 8,
        "expectations": "architecture skills, technical leadership, strategic thinking"
    },
    "Lead/Staff (8+ years)": {
        "min_years": 8,
        "max_years": 20,
        "expectations": "system architecture, team leadership, cross-team collaboration"
    }
}


def evaluate_candidate(
    resume_text: str, 
    job_description: str = "Software Engineer",
    company: str = "General",
    experience_level: str = "Mid-Level (3-5 years)"
) -> Optional[Dict]:
    """
    Autonomously evaluate a candidate based on their resume for a specific company and role.
    
    This function demonstrates autonomous decision-making by:
    1. Understanding the goal (evaluate candidate fit)
    2. Using AI to extract relevant information
    3. Calculating a fit score based on company and role requirements
    4. Returning structured data for decision-making
    
    Args:
        resume_text: Extracted text from candidate's resume
        job_description: Target job role
        company: Target company for interview preparation
        experience_level: Expected experience level
        
    Returns:
        Dictionary with candidate data and fit score, or None if evaluation fails
    """
    try:
        # Initialize LangChain ChatOpenAI with GPT-4o
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.3,  # Lower temperature for more consistent evaluation
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Get experience expectations
        exp_config = EXPERIENCE_EXPECTATIONS.get(
            experience_level, 
            EXPERIENCE_EXPECTATIONS["Mid-Level (3-5 years)"]
        )
        
        # Create evaluation prompt with company context
        evaluation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert technical recruiter evaluating candidates for a {job_description} position at {company}.

**Target Experience Level:** {experience_level}
**Expected Years:** {min_years}-{max_years} years
**Level Expectations:** {expectations}

Analyze the resume and extract the following information:
1. Candidate's full name
2. Key technical skills (list the most relevant ones for {job_description})
3. Years of experience (estimate if not explicitly stated)
4. Education background
5. Notable projects or achievements relevant to the role

Then, calculate a "Fit Score" from 0-100 based on:
- Technical skills match for {job_description} role (35 points)
- Years of experience alignment with {experience_level} (25 points)
- Company culture fit for {company} (15 points)
- Education and certifications relevance (10 points)
- Projects and achievements quality (15 points)

**Company-Specific Considerations:**
- If applying to Google: Value problem-solving, algorithms, system design
- If applying to Amazon: Value leadership principles, customer focus, ownership
- If applying to Microsoft: Value growth mindset, technical depth
- If applying to Meta: Value move fast, scale thinking, impact focus
- If applying to Apple: Value attention to detail, design thinking
- If applying to Netflix: Value high performance, independence
- If applying to Startup: Value versatility, adaptability, full-stack thinking
- For General: Standard industry expectations

Return your analysis as a valid JSON object with this exact structure:
{{
    "name": "Candidate Name",
    "skills": ["skill1", "skill2", "skill3"],
    "years_of_experience": 5,
    "education": "Degree information",
    "fit_score": 85,
    "reasoning": "Brief explanation of the score considering company and role fit",
    "strengths": ["strength1", "strength2"],
    "improvement_areas": ["area1", "area2"],
    "company_fit_notes": "Notes specific to {company} culture fit"
}}

Be objective and precise in your evaluation. Consider both technical fit and cultural alignment with {company}."""),
            ("human", "Resume content:\n\n{resume_text}")
        ])
        
        # Create the chain
        chain = evaluation_prompt | llm
        
        # Invoke the chain
        response = chain.invoke({
            "job_description": job_description,
            "company": company,
            "experience_level": experience_level,
            "min_years": exp_config["min_years"],
            "max_years": exp_config["max_years"],
            "expectations": exp_config["expectations"],
            "resume_text": resume_text
        })
        
        # Parse the response
        response_text = response.content.strip()
        
        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        # Parse JSON
        evaluation_data = json.loads(response_text)
        
        # Validate required fields
        required_fields = ["name", "skills", "years_of_experience", "fit_score"]
        for field in required_fields:
            if field not in evaluation_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Ensure fit_score is a number and within range
        evaluation_data["fit_score"] = max(0, min(100, int(evaluation_data["fit_score"])))
        
        # Add job description, company, and experience level to the evaluation data
        evaluation_data["job_description"] = job_description
        evaluation_data["company"] = company
        evaluation_data["experience_level"] = experience_level
        
        return evaluation_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing evaluation response as JSON: {str(e)}")
        if 'response_text' in locals():
            logger.debug(f"Response was: {response_text}")
        return None
    except Exception as e:
        logger.error(f"Error evaluating candidate: {str(e)}")
        return None


def format_evaluation_summary(evaluation_data: Dict, interview_settings: Dict = None) -> str:
    """
    Format evaluation data into a human-readable summary.
    
    Args:
        evaluation_data: Dictionary containing evaluation results
        interview_settings: Optional interview settings with company/role info
        
    Returns:
        Formatted summary string
    """
    skills_list = ", ".join(evaluation_data.get("skills", [])[:8])
    strengths = evaluation_data.get("strengths", [])
    improvements = evaluation_data.get("improvement_areas", [])
    company_notes = evaluation_data.get("company_fit_notes", "")
    
    company = evaluation_data.get("company", "General")
    if interview_settings:
        company = interview_settings.get("company", company)
    
    strengths_text = "\n".join([f"  - {s}" for s in strengths[:4]]) if strengths else "  - Not specified"
    improvements_text = "\n".join([f"  - {i}" for i in improvements[:3]]) if improvements else "  - Continue developing skills"
    
    summary = f"""## 📊 Candidate Evaluation Results

**Name:** {evaluation_data.get('name', 'Unknown')}
**Target Company:** {company}
**Position:** {evaluation_data.get('job_description', 'Software Engineer')}
**Experience Level:** {evaluation_data.get('experience_level', 'Not specified')}

### Qualifications
- **Skills:** {skills_list}
- **Experience:** {evaluation_data.get('years_of_experience', 'N/A')} years
- **Education:** {evaluation_data.get('education', 'Not specified')}

### Fit Score: {evaluation_data.get('fit_score', 0)}/100

### Key Strengths:
{strengths_text}

### Areas for Growth:
{improvements_text}

### Company Fit Assessment:
{company_notes if company_notes else 'Standard evaluation criteria applied.'}

---
*{evaluation_data.get('reasoning', 'No detailed reasoning provided')}*
"""
    
    return summary
