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


def evaluate_candidate(resume_text: str, job_description: str = "Python Developer") -> Optional[Dict]:
    """
    Autonomously evaluate a candidate based on their resume.
    
    This function demonstrates autonomous decision-making by:
    1. Understanding the goal (evaluate candidate fit)
    2. Using AI to extract relevant information
    3. Calculating a fit score
    4. Returning structured data for decision-making
    
    Args:
        resume_text: Extracted text from candidate's resume
        job_description: Target job role (default: "Python Developer")
        
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
        
        # Create evaluation prompt
        evaluation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert technical recruiter evaluating candidates for a {job_description} position.

Analyze the resume and extract the following information:
1. Candidate's full name
2. Key technical skills (list the most relevant ones)
3. Years of experience (estimate if not explicitly stated)
4. Education background
5. Notable projects or achievements

Then, calculate a "Fit Score" from 0-100 based on:
- Technical skills match (40 points)
- Years of experience (30 points)
- Education and certifications (15 points)
- Projects and achievements (15 points)

Return your analysis as a valid JSON object with this exact structure:
{{
    "name": "Candidate Name",
    "skills": ["skill1", "skill2", "skill3"],
    "years_of_experience": 5,
    "education": "Degree information",
    "fit_score": 85,
    "reasoning": "Brief explanation of the score"
}}

Be objective and precise in your evaluation."""),
            ("human", "Resume content:\n\n{resume_text}")
        ])
        
        # Create the chain
        chain = evaluation_prompt | llm
        
        # Invoke the chain
        response = chain.invoke({
            "job_description": job_description,
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
        
        # Add job description to the evaluation data
        evaluation_data["job_description"] = job_description
        
        return evaluation_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing evaluation response as JSON: {str(e)}")
        if 'response_text' in locals():
            logger.debug(f"Response was: {response_text}")
        return None
    except Exception as e:
        logger.error(f"Error evaluating candidate: {str(e)}")
        return None


def format_evaluation_summary(evaluation_data: Dict) -> str:
    """
    Format evaluation data into a human-readable summary.
    
    Args:
        evaluation_data: Dictionary containing evaluation results
        
    Returns:
        Formatted summary string
    """
    skills_list = ", ".join(evaluation_data.get("skills", [])[:5])
    
    summary = f"""## 📊 Candidate Evaluation Results

**Name:** {evaluation_data.get('name', 'Unknown')}
**Position:** {evaluation_data.get('job_description', 'Python Developer')}

### Qualifications
- **Skills:** {skills_list}
- **Experience:** {evaluation_data.get('years_of_experience', 'N/A')} years
- **Education:** {evaluation_data.get('education', 'Not specified')}

### Fit Score: {evaluation_data.get('fit_score', 0)}/100

{evaluation_data.get('reasoning', 'No reasoning provided')}
"""
    
    return summary
