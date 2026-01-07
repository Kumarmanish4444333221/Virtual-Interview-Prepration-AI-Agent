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


class InterviewAgent:
    """
    Autonomous interview agent that conducts conversational technical interviews.
    """
    
    def __init__(self, candidate_data: Dict):
        """
        Initialize the interview agent with candidate information.
        
        Args:
            candidate_data: Dictionary containing candidate evaluation results
        """
        self.candidate_data = candidate_data
        self.conversation_history = []
        self.questions_asked = 0
        self.max_questions = 5  # Conduct 5 interview questions
        
        # Initialize LangChain ChatOpenAI
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.7,  # Slightly higher for more natural conversation
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Create interview prompt template
        self.interview_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an experienced technical interviewer conducting a voice interview.

**Candidate Information:**
- Name: {name}
- Position: {position}
- Skills: {skills}
- Experience: {experience} years

**Interview Guidelines:**
1. Keep responses concise and conversational (2-3 sentences max) - this is a VOICE interview
2. Ask relevant technical questions based on their skills
3. Ask about their experience with specific projects
4. Be professional but friendly
5. Listen to their answers and ask follow-up questions
6. Evaluate their communication skills and technical knowledge

**Current Context:**
- Question #{question_num} of {max_questions}
- Previous conversation is provided below

Generate your next interview question or response based on the conversation context.
If this is the first question, start with a warm greeting and an opening question."""),
            ("human", "{input}")
        ])
    
    def generate_question(self, user_response: str = "") -> str:
        """
        Generate the next interview question or response.
        
        Args:
            user_response: The candidate's previous response (empty for first question)
            
        Returns:
            The interviewer's next question or response
        """
        try:
            # Build conversation context
            conversation_text = "\n".join([
                f"{'Interviewer' if i % 2 == 0 else 'Candidate'}: {msg}"
                for i, msg in enumerate(self.conversation_history)
            ])
            
            # Increment question counter if this is a new question
            if user_response or self.questions_asked == 0:
                if self.questions_asked > 0 or not user_response:
                    self.questions_asked += 1
            
            # Prepare input
            input_text = f"Previous conversation:\n{conversation_text}\n\n"
            if user_response:
                input_text += f"Candidate's latest response: {user_response}"
            else:
                input_text += "This is the start of the interview. Greet the candidate and ask your first question."
            
            # Generate response using the chain
            chain = self.interview_prompt | self.llm
            response = chain.invoke({
                "name": self.candidate_data.get("name", "Candidate"),
                "position": self.candidate_data.get("job_description", "Python Developer"),
                "skills": ", ".join(self.candidate_data.get("skills", [])[:5]),
                "experience": self.candidate_data.get("years_of_experience", "N/A"),
                "question_num": self.questions_asked,
                "max_questions": self.max_questions,
                "input": input_text
            })
            
            interviewer_message = response.content.strip()
            
            # Store in conversation history
            if user_response:
                self.conversation_history.append(user_response)
            self.conversation_history.append(interviewer_message)
            
            return interviewer_message
            
        except Exception as e:
            logger.error(f"Error generating interview question: {str(e)}")
            return "I apologize, but I'm having trouble generating the next question. Could you tell me more about your experience?"
    
    def should_conclude_interview(self) -> bool:
        """
        Determine if the interview should be concluded.
        
        Returns:
            True if interview should end, False otherwise
        """
        return self.questions_asked >= self.max_questions
    
    def generate_summary(self) -> str:
        """
        Generate a comprehensive interview summary.
        
        Returns:
            Formatted interview summary
        """
        try:
            # Create summary prompt
            summary_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert technical recruiter creating a comprehensive interview summary.

**Candidate Information:**
- Name: {name}
- Position Applied: {position}
- Initial Fit Score: {fit_score}/100

**Interview Conversation:**
{conversation}

Create a detailed interview summary including:
1. Overall Assessment (paragraph)
2. Technical Competency (rating and explanation)
3. Communication Skills (rating and explanation)
4. Key Strengths (bullet points)
5. Areas for Improvement (bullet points)
6. Final Recommendation (Strongly Recommend / Recommend / Consider / Do Not Recommend)

Be honest, professional, and constructive in your evaluation."""),
                ("human", "Generate the interview summary based on the conversation above.")
            ])
            
            # Format conversation
            conversation_text = ""
            for i, msg in enumerate(self.conversation_history):
                speaker = "Interviewer" if i % 2 == 0 else "Candidate"
                conversation_text += f"{speaker}: {msg}\n\n"
            
            # Generate summary
            chain = summary_prompt | self.llm
            response = chain.invoke({
                "name": self.candidate_data.get("name", "Candidate"),
                "position": self.candidate_data.get("job_description", "Python Developer"),
                "fit_score": self.candidate_data.get("fit_score", 0),
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
                f.write("AUTONOMOUS RECRUITMENT AGENT - INTERVIEW REPORT\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Candidate: {self.candidate_data.get('name', 'Unknown')}\n")
                f.write(f"Position: {self.candidate_data.get('job_description', 'Python Developer')}\n")
                f.write(f"Initial Fit Score: {self.candidate_data.get('fit_score', 0)}/100\n\n")
                f.write("-" * 80 + "\n")
                f.write("INTERVIEW TRANSCRIPT\n")
                f.write("-" * 80 + "\n\n")
                
                for i, msg in enumerate(self.conversation_history):
                    speaker = "Interviewer" if i % 2 == 0 else "Candidate"
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
