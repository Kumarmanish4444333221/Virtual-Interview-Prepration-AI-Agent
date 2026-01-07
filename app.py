"""
Autonomous Recruitment & Interview Agent
Main Chainlit application entry point
"""
import os
import tempfile
from dotenv import load_dotenv
import chainlit as cl
from modules.pdf_processor import extract_text, validate_pdf
from modules.evaluator import evaluate_candidate, format_evaluation_summary
from modules.audio_handler import transcribe_chainlit_audio, text_to_speech, transcribe_audio
from modules.interviewer import InterviewAgent

# Load environment variables
load_dotenv()

# Verify API key is available
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found in environment variables. Please create a .env file with your API key.")


@cl.on_audio_chunk
async def on_audio_chunk(chunk):
    """
    Handle incoming audio chunks from user voice input.
    Accumulates audio data for later transcription.
    """
    if chunk.isStart:
        # Initialize a buffer for audio chunks
        buffer = cl.user_session.get("audio_buffer")
        if buffer is None:
            buffer = []
        buffer.clear()
        cl.user_session.set("audio_buffer", buffer)
        cl.user_session.set("audio_mime_type", chunk.mimeType)
    
    # Append chunk data to buffer
    buffer = cl.user_session.get("audio_buffer")
    if buffer is not None:
        buffer.append(chunk.data)


@cl.on_audio_end
async def on_audio_end(elements):
    """
    Handle the end of audio recording from user.
    Transcribes the audio and processes it as interview response.
    """
    state = cl.user_session.get("state")
    
    # Get the audio buffer
    audio_buffer = cl.user_session.get("audio_buffer")
    audio_mime_type = cl.user_session.get("audio_mime_type", "audio/webm")
    
    if not audio_buffer:
        await cl.Message(content="⚠️ No audio data received. Please try again.").send()
        return
    
    # Combine all chunks into a single audio file
    audio_data = b"".join(audio_buffer)
    
    # Determine file extension based on mime type
    ext = ".webm"
    if "wav" in audio_mime_type:
        ext = ".wav"
    elif "mp3" in audio_mime_type:
        ext = ".mp3"
    elif "ogg" in audio_mime_type:
        ext = ".ogg"
    
    # Save to temp file for transcription
    temp_dir = tempfile.gettempdir()
    audio_file_path = os.path.join(temp_dir, f"user_audio_{os.getpid()}{ext}")
    
    try:
        with open(audio_file_path, "wb") as f:
            f.write(audio_data)
        
        # Transcribe the audio
        async with cl.Step(name="🎤 Transcribing Audio", type="tool") as step:
            transcribed_text = transcribe_audio(audio_file_path)
            
            if transcribed_text:
                step.output = f"✓ Transcribed: {transcribed_text}"
                
                # Show what was transcribed
                await cl.Message(content=f"🎤 *You said:* {transcribed_text}", author="User").send()
                
                # Process based on state
                if state == "interview":
                    await handle_interview_response(transcribed_text)
                else:
                    await cl.Message(content="⏳ Please upload a resume PDF file first to start the evaluation process.").send()
            else:
                step.output = "✗ Failed to transcribe audio"
                await cl.Message(content="⚠️ Could not transcribe audio. Please try again or type your response.").send()
    
    except Exception as e:
        print(f"Error processing audio: {str(e)}")
        await cl.Message(content="⚠️ Error processing audio. Please try again or type your response.").send()
    
    finally:
        # Clean up temp file
        if os.path.exists(audio_file_path):
            try:
                os.remove(audio_file_path)
            except:
                pass
        # Clear the buffer
        cl.user_session.set("audio_buffer", None)


@cl.on_chat_start
async def start():
    """
    Initialize the chat session and display welcome message.
    This is the entry point for autonomous agent behavior.
    """
    # Initialize session variables for autonomous decision tracking
    cl.user_session.set("state", "awaiting_resume")
    cl.user_session.set("candidate_data", None)
    cl.user_session.set("interviewer", None)
    cl.user_session.set("interview_count", 0)
    cl.user_session.set("audio_buffer", None)
    
    # Welcome message with clear instructions
    welcome_msg = """## 🎙️ Virtual Interview Preparation AI Agent.

Welcome! I'm your autonomous AI recruiter. 

**How it works:**
1. 📄 Upload a resume (PDF format)
2. 🤖 I'll autonomously analyze the candidate
3. ✅ If qualified (score ≥ 75%), I'll conduct a voice interview
4. ❌ If not qualified, I'll provide feedback

Please **upload a resume** to begin the recruitment process.
"""
    
    await cl.Message(content=welcome_msg).send()


@cl.on_message
async def main(message: cl.Message):
    """
    Handle incoming messages and demonstrate autonomous behavior.
    """
    state = cl.user_session.get("state")
    
    # Check if resume was uploaded with the message
    if message.elements:
        # Handle file uploads
        for element in message.elements:
            if hasattr(element, 'mime') and element.mime == "application/pdf":
                await handle_file_upload(message.elements)
                return
    
    # Handle audio messages in interview mode
    if state == "interview":
        # Check for audio input
        user_input = message.content
        
        # Process audio if present
        if message.elements:
            for element in message.elements:
                if hasattr(element, 'mime') and 'audio' in element.mime:
                    async with cl.Step(name="🎤 Transcribing Audio", type="tool") as step:
                        transcribed_text = transcribe_chainlit_audio(element)
                        if transcribed_text:
                            user_input = transcribed_text
                            step.output = f"✓ Transcribed: {transcribed_text}"
                        else:
                            step.output = "✗ Failed to transcribe audio"
                            await cl.Message(content="⚠️ Could not transcribe audio. Please try again or type your response.").send()
                            return
        
        if not user_input or not user_input.strip():
            await cl.Message(content="Please provide a response (voice or text).").send()
            return
        
        await handle_interview_response(user_input)
        return
    
    if state == "awaiting_resume":
        await cl.Message(
            content="⏳ Please upload a resume PDF file to start the evaluation process."
        ).send()
    elif state == "rejected":
        await cl.Message(
            content="This candidate has been evaluated and did not meet requirements. Please upload a new resume to evaluate another candidate."
        ).send()
    else:
        await cl.Message(
            content="System in unknown state. Please refresh and try again."
        ).send()


async def handle_interview_response(user_input: str):
    """
    Handle candidate responses during the interview.
    Demonstrates autonomous conversation and decision-making.
    """
    interviewer = cl.user_session.get("interviewer")
    
    if not interviewer:
        await cl.Message(content="⚠️ Interview session not initialized. Please restart.").send()
        return
    
    # Generate interviewer's response
    async with cl.Step(name="🤔 Generating Response", type="tool") as step:
        interviewer_response = interviewer.generate_question(user_input)
        step.output = f"✓ Generated response ({len(interviewer_response)} chars)"
    
    # Check if interview should conclude
    if interviewer.should_conclude_interview():
        # Send final question/response
        await send_voice_message(interviewer_response)
        
        # Generate and save summary
        async with cl.Step(name="📝 Generating Interview Summary", type="tool") as step:
            step.output = "Creating comprehensive interview report..."
            summary = interviewer.generate_summary()
            
            # Save to file
            report_saved = interviewer.save_interview_report(summary)
            if report_saved:
                step.output = "✓ Interview report saved to interview_report.txt"
            else:
                step.output = "⚠️ Could not save report to file, but summary generated"
        
        # Send conclusion message
        await cl.Message(
            content=f"## 🎉 Interview Complete!\n\nThank you for your time. Here's your interview summary:\n\n{summary}\n\n---\n\n{'✓ A detailed report has been saved to `interview_report.txt`' if report_saved else ''}"
        ).send()
        
        # Update state
        cl.user_session.set("state", "completed")
    else:
        # Continue interview - send next question with voice
        await send_voice_message(interviewer_response)


async def send_voice_message(text: str):
    """
    Send a message with both text and audio (TTS).
    
    Args:
        text: Message text to send
    """
    try:
        # Generate audio
        async with cl.Step(name="🔊 Generating Speech", type="tool") as step:
            audio_path = text_to_speech(text)
            if audio_path:
                step.output = "✓ Audio generated"
            else:
                step.output = "⚠️ Audio generation failed, using text only"
        
        # Send message with audio element if available
        if audio_path and os.path.exists(audio_path):
            elements = [
                cl.Audio(
                    name="interviewer_audio",
                    path=audio_path,
                    display="inline",
                    auto_play=True
                )
            ]   
            await cl.Message(content=text, elements=elements).send()
        else:
            # Fallback to text only
            await cl.Message(content=text).send()
            
    except Exception as e:
        print(f"Error sending voice message: {str(e)}")
        # Fallback to text only
        await cl.Message(content=text).send()


async def handle_file_upload(elements):
    """
    Handle file uploads and trigger autonomous evaluation.
    This demonstrates autonomous behavior: Goal Understanding → Task Decomposition → Decision Making
    """
    for element in elements:
        if isinstance(element, cl.File):
            # Only process PDF files
            if not element.name.lower().endswith('.pdf'):
                await cl.Message(
                    content="❌ Please upload a PDF file. Other file types are not supported."
                ).send()
                return
            
            # Step 1: Reading Resume (Task Decomposition)
            async with cl.Step(name="🧠 Reading Resume", type="tool") as step:
                step.output = "Extracting text from uploaded PDF..."
                
                # Extract text from PDF
                resume_text = extract_text(element.path)
                
                if not resume_text:
                    await cl.Message(
                        content="❌ Failed to extract text from the PDF. Please ensure the file is a valid, readable PDF document."
                    ).send()
                    return
                
                step.output = f"✓ Successfully extracted {len(resume_text)} characters from resume"
            
            # Step 2: Analyzing Skills (Task Decomposition)
            async with cl.Step(name="🤔 Analyzing Skills & Experience", type="tool") as step:
                step.output = "Evaluating candidate qualifications using AI..."
                
                # Evaluate candidate using LangChain and GPT-4o
                evaluation_data = evaluate_candidate(resume_text)
                
                if not evaluation_data:
                    await cl.Message(
                        content="❌ Failed to evaluate the candidate. Please try again or check the resume format."
                    ).send()
                    return
                
                # Store candidate data in session
                cl.user_session.set("candidate_data", evaluation_data)
                
                step.output = f"✓ Evaluation complete: {evaluation_data.get('name', 'Unknown')} - Score: {evaluation_data.get('fit_score', 0)}/100"
            
            # Step 3: Calculating Fit Score (Task Decomposition)
            async with cl.Step(name="📊 Calculating Fit Score", type="tool") as step:
                fit_score = evaluation_data.get('fit_score', 0)
                step.output = f"Fit Score: {fit_score}/100"
                
                # Display evaluation summary
                summary = format_evaluation_summary(evaluation_data)
                await cl.Message(content=summary).send()
            
            # Step 4: Autonomous Decision Making
            async with cl.Step(name="🎯 Making Decision", type="tool") as step:
                fit_score = evaluation_data.get('fit_score', 0)
                
                # AUTONOMOUS DECISION: Score >= 75 → Interview, else Reject
                if fit_score >= 75:
                    step.output = f"✓ Score {fit_score} >= 75: Proceeding to interview"
                    cl.user_session.set("state", "interview")
                    
                    # Initialize interview agent
                    interviewer = InterviewAgent(evaluation_data)
                    cl.user_session.set("interviewer", interviewer)
                    
                    await cl.Message(
                        content=f"✅ **Excellent match!** {evaluation_data.get('name', 'Candidate')} has scored {fit_score}/100.\n\n🎙️ **Starting Interview Mode...**\n\nI'll now conduct a voice interview. You can speak or type your responses."
                    ).send()
                    
                    # Start the interview with the first question
                    first_question = interviewer.generate_question()
                    await send_voice_message(first_question)
                else:
                    step.output = f"✗ Score {fit_score} < 75: Candidate does not meet requirements"
                    cl.user_session.set("state", "rejected")
                    
                    await cl.Message(
                        content=f"❌ **Candidate does not meet requirements.**\n\n{evaluation_data.get('name', 'Candidate')} scored {fit_score}/100, which is below the threshold of 75.\n\n**Feedback:** While the candidate shows some potential, they do not currently meet the minimum requirements for this position. We recommend gaining more experience in the required technical skills."
                    ).send()
            
            return


if __name__ == "__main__":
    # This allows the app to be run directly, though Chainlit should be used via CLI
    print("Please run this app using: chainlit run app.py")
