"""
Interviewer Module
Handles conversational interview logic with voice support
"""
import os
import logging
from typing import Dict, List, Tuple
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, AIMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Company interview styles
COMPANY_INTERVIEW_STYLES = {
    "Google": {
        "style": "Focus on problem-solving, algorithms, and system design. Use the STAR method for behavioral questions. Ask about past projects and how candidates approach complex problems.",
        "question_types": ["algorithmic thinking", "system design", "behavioral (STAR)", "coding best practices", "scalability"],
        "evaluation_focus": "Problem-solving ability, technical depth, collaboration skills"
    },
    "Amazon": {
        "style": "Center questions around Leadership Principles. Focus on customer obsession, ownership, and bias for action. Use behavioral questions with STAR format.",
        "question_types": ["leadership principles", "customer focus", "ownership examples", "dive deep scenarios", "deliver results"],
        "evaluation_focus": "Leadership potential, customer obsession, ability to deliver"
    },
    "Microsoft": {
        "style": "Evaluate growth mindset, technical excellence, and collaborative problem-solving. Ask about learning from failures and continuous improvement.",
        "question_types": ["growth mindset", "technical depth", "collaboration", "innovation", "learning ability"],
        "evaluation_focus": "Growth mindset, technical skills, teamwork"
    },
    "Meta": {
        "style": "Focus on moving fast, building at scale, and making impact. Ask about handling ambiguity and building products that matter.",
        "question_types": ["scale thinking", "impact focus", "move fast mentality", "product sense", "technical excellence"],
        "evaluation_focus": "Speed of execution, impact orientation, technical skills"
    },
    "Apple": {
        "style": "Emphasize attention to detail, design thinking, and pursuit of excellence. Ask about quality focus and user experience considerations.",
        "question_types": ["attention to detail", "design thinking", "quality focus", "user experience", "innovation"],
        "evaluation_focus": "Quality mindset, design sense, technical excellence"
    },
    "Netflix": {
        "style": "Focus on freedom and responsibility, high performance culture, and candid communication. Ask about autonomous decision-making.",
        "question_types": ["independent judgment", "candid feedback", "high performance", "culture fit", "innovation"],
        "evaluation_focus": "Independence, high performance, cultural alignment"
    },
    "Startup": {
        "style": "Evaluate versatility, adaptability, and willingness to wear multiple hats. Focus on resourcefulness and growth potential.",
        "question_types": ["adaptability", "full-stack thinking", "resourcefulness", "growth potential", "ownership"],
        "evaluation_focus": "Versatility, adaptability, entrepreneurial mindset"
    },
    "General": {
        "style": "Standard technical interview with behavioral components. Balance technical questions with soft skills assessment.",
        "question_types": ["technical skills", "problem-solving", "teamwork", "communication", "career goals"],
        "evaluation_focus": "Overall fit, technical competency, communication skills"
    }
}

EXPERIENCE_LEVEL_CONFIGS = {
    "Fresher (0-1 years)": {
        "difficulty": "entry-level",
        "focus": "fundamentals, learning ability, academic projects, enthusiasm",
        "question_style": "Focus on basic concepts, learning potential, and academic/internship projects. Be encouraging and supportive."
    },
    "Junior (1-3 years)": {
        "difficulty": "intermediate",
        "focus": "practical experience, code quality, teamwork, growth trajectory",
        "question_style": "Ask about real-world project experience, challenges faced, and lessons learned. Moderate technical depth."
    },
    "Mid-Level (3-5 years)": {
        "difficulty": "intermediate-advanced",
        "focus": "technical depth, system design basics, mentoring, complex problem solving",
        "question_style": "Deeper technical questions, basic system design, leadership potential. Expect well-articulated answers."
    },
    "Senior (5-8 years)": {
        "difficulty": "advanced",
        "focus": "architecture, technical leadership, strategic thinking, mentoring",
        "question_style": "Complex system design, technical leadership scenarios, cross-team collaboration. Expect expert-level responses."
    },
    "Lead/Staff (8+ years)": {
        "difficulty": "expert",
        "focus": "system architecture, organizational impact, technical strategy, team building",
        "question_style": "Architecture decisions, organizational impact, technical vision. Expect thought leadership and strategic thinking."
    }
}


class InterviewAgent:
    """
    Autonomous interview agent that conducts conversational technical interviews
    customized for specific companies and experience levels.
    """
    
    def __init__(
        self, 
        candidate_data: Dict,
        company: str = "General",
        experience_level: str = "Mid-Level (3-5 years)",
        max_questions: int = 7
    ):
        """
        Initialize the interview agent with candidate information and interview context.
        
        Args:
            candidate_data: Dictionary containing candidate evaluation results
            company: Target company for interview style
            experience_level: Candidate's experience level
            max_questions: Number of questions to ask
        """
        self.candidate_data = candidate_data
        self.company = company
        self.experience_level = experience_level
        self.conversation_history = []
        self.questions_asked = 0
        self.max_questions = max_questions
        self.responses_received = 0
        
        # Get company and experience configurations
        self.company_config = COMPANY_INTERVIEW_STYLES.get(company, COMPANY_INTERVIEW_STYLES["General"])
        self.experience_config = EXPERIENCE_LEVEL_CONFIGS.get(
            experience_level, 
            EXPERIENCE_LEVEL_CONFIGS["Mid-Level (3-5 years)"]
        )
        
        # Initialize LangChain ChatOpenAI
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.7,  # Slightly higher for more natural conversation
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Create interview prompt template
        self.interview_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an experienced technical interviewer conducting a mock interview for {company}.

**Candidate Information:**
- Name: {name}
- Position: {position}
- Skills: {skills}
- Experience: {experience} years
- Target Level: {experience_level}

**Interview Style for {company}:**
{company_style}

**Question Types to Cover:** {question_types}

**Experience Level Guidelines ({experience_level}):**
{experience_guidelines}

**Interview Guidelines:**
1. Keep responses conversational and natural (2-4 sentences for questions)
2. Ask ONE clear question at a time - wait for the answer before asking the next
3. Mix technical questions with behavioral questions appropriate for {company}
4. Adjust difficulty based on {experience_level} level
5. Be professional but friendly and encouraging
6. Listen to answers and ask relevant follow-up questions
7. Cover different aspects: technical skills, problem-solving, behavioral, and culture fit

**Current Progress:**
- This is Question #{question_num} of {max_questions}
- Questions asked so far: {questions_asked}
- Responses received: {responses_received}

**IMPORTANT:** 
- If this is the first question, start with a warm greeting mentioning {company} and ask an opening question.
- Ask exactly ONE question and WAIT for the candidate to respond.
- After receiving an answer, acknowledge it briefly and then ask your next question.
- Make questions progressively cover different areas (technical, behavioral, situational).
- Ensure questions are appropriate for someone interviewing at {company}."""),
            ("human", "{input}")
        ])
    
    def add_candidate_response(self, response: str):
        """
        Add the candidate's response to the conversation history.
        
        Args:
            response: The candidate's response text
        """
        self.conversation_history.append(("Candidate", response))
        self.responses_received += 1
    
    def generate_question(self) -> str:
        """
        Generate the next interview question.
        
        Returns:
            The interviewer's next question
        """
        try:
            # Build conversation context
            conversation_text = ""
            for speaker, msg in self.conversation_history:
                conversation_text += f"{speaker}: {msg}\n\n"
            
            # Increment question counter
            self.questions_asked += 1
            
            # Prepare input based on conversation state
            if not self.conversation_history:
                input_text = f"This is the START of the interview. Greet {self.candidate_data.get('name', 'the candidate')} warmly, mention that this is a mock interview for {self.company}, and ask your FIRST interview question."
            else:
                last_response = self.conversation_history[-1][1] if self.conversation_history else ""
                input_text = f"""Previous conversation:
{conversation_text}

The candidate just responded: "{last_response}"

Briefly acknowledge their response (1 sentence), then ask Question #{self.questions_asked}. 
Remember to cover different areas and adjust for {self.experience_level} level.
Ask ONE clear question and wait for response."""
            
            # Generate response using the chain
            chain = self.interview_prompt | self.llm
            response = chain.invoke({
                "company": self.company,
                "name": self.candidate_data.get("name", "Candidate"),
                "position": self.candidate_data.get("job_description", "Software Engineer"),
                "skills": ", ".join(self.candidate_data.get("skills", [])[:6]),
                "experience": self.candidate_data.get("years_of_experience", "N/A"),
                "experience_level": self.experience_level,
                "company_style": self.company_config["style"],
                "question_types": ", ".join(self.company_config["question_types"]),
                "experience_guidelines": self.experience_config["question_style"],
                "question_num": self.questions_asked,
                "max_questions": self.max_questions,
                "questions_asked": self.questions_asked,
                "responses_received": self.responses_received,
                "input": input_text
            })
            
            interviewer_message = response.content.strip()
            
            # Store in conversation history
            self.conversation_history.append(("Interviewer", interviewer_message))
            
            return interviewer_message
            
        except Exception as e:
            logger.error(f"Error generating interview question: {str(e)}")
            return f"Thank you for that response. Could you tell me more about your experience with {self.candidate_data.get('skills', ['technology'])[0] if self.candidate_data.get('skills') else 'your technical skills'}?"
    
    def should_conclude_interview(self) -> bool:
        """
        Determine if the interview should be concluded.
        Interview ends when we've asked all questions AND received all responses.
        
        Returns:
            True if interview should end, False otherwise
        """
        # We conclude after receiving the response to the last question
        return self.responses_received >= self.max_questions
    
    def generate_summary(self) -> str:
        """
        Generate a comprehensive interview summary tailored to the target company.
        
        Returns:
            Formatted interview summary
        """
        try:
            # Create summary prompt
            summary_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert technical recruiter creating a comprehensive interview summary for a candidate interviewing at {company}.

**Candidate Information:**
- Name: {name}
- Position Applied: {position}
- Target Company: {company}
- Experience Level: {experience_level}
- Initial Fit Score: {fit_score}/100

**{company} Evaluation Focus:**
{evaluation_focus}

**Interview Conversation:**
{conversation}

Create a detailed, {company}-focused interview summary including:

1. **Overall Assessment** (2-3 paragraphs)
   - General impression and interview performance
   - Alignment with {company}'s culture and values
   
2. **Technical Competency** (X/10 rating with explanation)
   - Depth of technical knowledge
   - Problem-solving approach
   - Relevance to the role
   
3. **Communication Skills** (X/10 rating with explanation)
   - Clarity of expression
   - Ability to articulate complex ideas
   - Professional demeanor
   
4. **{company} Culture Fit** (X/10 rating with explanation)
   - Alignment with company values
   - Work style compatibility
   
5. **Key Strengths** (bullet points)
   - Top 4-5 strengths demonstrated
   
6. **Areas for Improvement** (bullet points)
   - 3-4 specific areas to work on before a real {company} interview
   
7. **Preparation Tips for {company}** (bullet points)
   - Specific advice for improving chances at {company}
   
8. **Final Recommendation**
   - One of: Strongly Recommend / Recommend / Consider with Preparation / More Preparation Needed
   - Brief justification

Be honest, professional, and constructive. Provide actionable feedback that will help the candidate prepare for a real interview at {company}."""),
                ("human", "Generate the interview summary based on the conversation above.")
            ])
            
            # Format conversation
            conversation_text = ""
            for speaker, msg in self.conversation_history:
                conversation_text += f"{speaker}: {msg}\n\n"
            
            # Generate summary
            chain = summary_prompt | self.llm
            response = chain.invoke({
                "company": self.company,
                "name": self.candidate_data.get("name", "Candidate"),
                "position": self.candidate_data.get("job_description", "Software Engineer"),
                "experience_level": self.experience_level,
                "fit_score": self.candidate_data.get("fit_score", 0),
                "evaluation_focus": self.company_config["evaluation_focus"],
                "conversation": conversation_text
            })
            
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating interview summary: {str(e)}")
            return "Error generating summary. Please review the conversation history manually."
    
    def save_interview_report(self, summary: str, output_path: str = "interview_report.txt") -> bool:
        """
        Save the interview report to a file.
        
        Args:
            summary: Interview summary text
            output_path: Path to save the report
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("=" * 80 + "\n")
                f.write("VIRTUAL INTERVIEW PREPARATION - INTERVIEW REPORT\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Candidate: {self.candidate_data.get('name', 'Unknown')}\n")
                f.write(f"Target Company: {self.company}\n")
                f.write(f"Position: {self.candidate_data.get('job_description', 'Software Engineer')}\n")
                f.write(f"Experience Level: {self.experience_level}\n")
                f.write(f"Initial Fit Score: {self.candidate_data.get('fit_score', 0)}/100\n")
                f.write(f"Questions Asked: {self.questions_asked}\n\n")
                f.write("-" * 80 + "\n")
                f.write("INTERVIEW TRANSCRIPT\n")
                f.write("-" * 80 + "\n\n")
                
                for speaker, msg in self.conversation_history:
                    f.write(f"{speaker}: {msg}\n\n")
                
                f.write("-" * 80 + "\n")
                f.write("INTERVIEW SUMMARY\n")
                f.write("-" * 80 + "\n\n")
                f.write(summary)
                f.write("\n\n" + "=" * 80 + "\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving interview report: {str(e)}")
            return False
