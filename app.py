"""
Virtual Interview Preparation AI Agent
Main Chainlit application entry point
"""
import os
import tempfile
import asyncio
from dotenv import load_dotenv
import chainlit as cl
from modules.pdf_processor import extract_text, validate_pdf
from modules.evaluator import evaluate_candidate, format_evaluation_summary
from modules.audio_handler import transcribe_chainlit_audio, text_to_speech, transcribe_audio
from modules.interviewer import InterviewAgent
from modules.auth import authenticate_user, register_user, user_exists
from modules.history import save_interview, get_user_interviews, get_user_stats

# Load environment variables
load_dotenv()

# Verify API key is available
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found in environment variables. Please create a .env file with your API key.")


# ---------------------------------------------------------------------------
# Authentication – Chainlit password auth callback
# ---------------------------------------------------------------------------
# The login form is shown automatically by Chainlit when this callback exists.
# New users are registered on their first login attempt.
# ---------------------------------------------------------------------------

@cl.password_auth_callback
async def auth_callback(username: str, password: str):
    """Authenticate or auto-register a user."""
    if not username or not password:
        return None

    if user_exists(username):
        user_data = authenticate_user(username, password)
        if user_data is None:
            return None
        return cl.User(
            identifier=user_data["username"],
            display_name=user_data["display_name"],
            metadata={"created_at": user_data["created_at"]},
        )

    # First-time login → auto-register
    registered = register_user(username, password)
    if not registered:
        return None
    return cl.User(
        identifier=username,
        display_name=username,
        metadata={"new_user": True},
    )


def _get_username() -> str:
    """Return the authenticated user's identifier from the current session."""
    user = cl.user_session.get("user")
    if user is None:
        raise RuntimeError("No authenticated user in session")
    return user.identifier


# Company presets with interview styles
COMPANY_PRESETS = {
    "Google": {
        "style": "Problem-solving, algorithms, system design, STAR behavioral",
        "culture": "Innovation, collaboration, data-driven decisions",
        "emoji": "🔍"
    },
    "Amazon": {
        "style": "Leadership Principles, behavioral STAR, system design",
        "culture": "Customer obsession, ownership, bias for action",
        "emoji": "📦"
    },
    "Microsoft": {
        "style": "Technical depth, growth mindset, problem-solving",
        "culture": "Growth mindset, diversity, innovation",
        "emoji": "🪟"
    },
    "Meta": {
        "style": "Move fast, system design at scale, impact focus",
        "culture": "Move fast, be bold, focus on impact",
        "emoji": "👤"
    },
    "Apple": {
        "style": "Design thinking, attention to detail, excellence",
        "culture": "Innovation, quality, user experience",
        "emoji": "🍎"
    },
    "Netflix": {
        "style": "Culture fit, high performance, freedom & responsibility",
        "culture": "Freedom and responsibility, high performance",
        "emoji": "🎬"
    },
    "Startup": {
        "style": "Versatility, adaptability, full-stack thinking",
        "culture": "Fast-paced, wear multiple hats, growth",
        "emoji": "🚀"
    },
    "Other Company": {
        "style": "Standard technical interview with behavioral components",
        "culture": "Professional environment with growth opportunities",
        "emoji": "🏢"
    }
}

EXPERIENCE_LEVELS = {
    "Fresher (0-1 years)": {
        "level": "entry",
        "focus": "Fundamentals, learning ability, projects",
        "question_difficulty": "Basic to intermediate",
        "emoji": "🌱"
    },
    "Junior (1-3 years)": {
        "level": "junior",
        "focus": "Practical experience, code quality, teamwork",
        "question_difficulty": "Intermediate",
        "emoji": "📗"
    },
    "Mid-Level (3-5 years)": {
        "level": "mid",
        "focus": "System design, leadership potential",
        "question_difficulty": "Intermediate to advanced",
        "emoji": "📘"
    },
    "Senior (5-8 years)": {
        "level": "senior",
        "focus": "Architecture, technical leadership",
        "question_difficulty": "Advanced",
        "emoji": "📙"
    },
    "Lead/Staff (8+ years)": {
        "level": "lead",
        "focus": "System architecture, team leadership",
        "question_difficulty": "Expert level",
        "emoji": "📕"
    }
}

ROLE_CATEGORIES = {
    "Engineering": [
        "Software Engineer",
        "Frontend Developer", 
        "Backend Developer",
        "Full Stack Developer",
        "Mobile Developer",
        "DevOps Engineer",
        "Cloud Engineer",
        "QA Engineer",
        "Security Engineer"
    ],
    "Data & AI": [
        "Data Scientist",
        "Data Engineer", 
        "ML Engineer",
        "Data Analyst",
        "AI Engineer"
    ],
    "Specialized": [
        "Python Developer",
        "Java Developer",
        "JavaScript Developer",
        "React Developer",
        "Node.js Developer",
        "iOS Developer",
        "Android Developer",
        "Golang Developer"
    ],
    "Management": [
        "Engineering Manager",
        "Tech Lead",
        "Product Manager",
        "Scrum Master"
    ]
}


@cl.on_audio_start
async def on_audio_start():
    """
    Handle the start of audio recording.
    Initialize the audio buffer.
    """
    cl.user_session.set("stop_audio", True)
    cl.user_session.set("audio_buffer", [])
    cl.user_session.set("audio_mime_type", "audio/webm")


@cl.on_audio_chunk
async def on_audio_chunk(chunk):
    """
    Handle incoming audio chunks from user voice input.
    Accumulates audio data for later transcription.
    """
    # Initialize buffer if this is the start
    if chunk.isStart:
        cl.user_session.set("stop_audio", True)
        cl.user_session.set("audio_buffer", [])
        cl.user_session.set("audio_mime_type", chunk.mimeType)
    
    # Append chunk data to buffer
    buffer = cl.user_session.get("audio_buffer")
    if buffer is not None:
        buffer.append(chunk.data)
        cl.user_session.set("audio_buffer", buffer)


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
        await cl.Message(content="⚠️ No audio detected. Please try again.").send()
        return
    
    # Combine all chunks into a single audio file
    audio_data = b"".join(audio_buffer)
    
    # Check if audio data is too small (likely empty recording)
    if len(audio_data) < 1000:
        await cl.Message(content="⚠️ Recording too short. Please speak for longer.").send()
        cl.user_session.set("audio_buffer", None)
        return
    
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
        await cl.Message(content="🎤 *Processing your voice...*").send()
        
        transcribed_text = transcribe_audio(audio_file_path)
        
        if transcribed_text and transcribed_text.strip():
            # Show what was transcribed
            await cl.Message(content=f"💬 **You said:** {transcribed_text}").send()
            
            # Process based on state
            if state == "interview":
                await handle_interview_response(transcribed_text)
            elif state == "awaiting_resume":
                await cl.Message(content="📄 Please upload your resume (PDF) to start the interview.").send()
            else:
                await cl.Message(content="👆 Please complete the setup first using the buttons above.").send()
        else:
            await cl.Message(
                content="⚠️ Couldn't understand the audio. Please speak clearly or type your response."
            ).send()
    
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
    Initialize the chat session and display welcome message with interactive setup.
    """
    # Initialize session variables
    cl.user_session.set("state", "setup_company")
    cl.user_session.set("candidate_data", None)
    cl.user_session.set("interviewer", None)
    cl.user_session.set("interview_count", 0)
    cl.user_session.set("audio_buffer", None)
    cl.user_session.set("stop_audio", False)
    cl.user_session.set("interview_settings", {
        "company": None,
        "role": None,
        "experience": None,
        "num_questions": 7
    })

    # Build personalised greeting
    username = _get_username()
    stats = get_user_stats(username)

    stats_block = ""
    if stats["total_interviews"] > 0:
        stats_block = f"""
### 📈 Your Dashboard
| Stat | Value |
|------|-------|
| 🎯 **Total Interviews** | {stats['total_interviews']} |
| 📊 **Average Fit Score** | {stats['avg_score']}/100 |
| 🏆 **Best Fit Score** | {stats['best_score']}/100 |
| 🏢 **Companies Practiced** | {stats['companies_practiced']} |

"""

    welcome_msg = f"""## 🤖 Virtual Interview Preparation AI Agent

Welcome back, **{username}**! I'm your AI interview coach.

### ✨ What I can do:
- 🎯 **Company-specific interviews** - Practice for Google, Amazon, Microsoft & more
- 🎤 **Voice & text responses** - Answer naturally using voice or keyboard  
- 📊 **Detailed feedback** - Get actionable insights to improve
- 📜 **Interview history** - Track your progress over time
{stats_block}
---

### Let's set up your practice interview!

**Step 1 of 4:** Which company are you preparing for?"""

    actions = []
    if stats["total_interviews"] > 0:
        actions.append(
            cl.Action(name="view_history", payload={}, label="📜 View Interview History")
        )

    await cl.Message(content=welcome_msg, actions=actions).send()

    # Show company selection buttons
    await show_company_selection()


async def show_company_selection():
    """Display company selection with action buttons."""
    actions = []
    for company, info in COMPANY_PRESETS.items():
        actions.append(
            cl.Action(
                name="select_company",
                payload={"company": company},
                label=f"{info['emoji']} {company}"
            )
        )
    
    await cl.Message(
        content="👇 **Select your target company:**",
        actions=actions
    ).send()


async def show_experience_selection():
    """Display experience level selection with action buttons."""
    actions = []
    for level, info in EXPERIENCE_LEVELS.items():
        actions.append(
            cl.Action(
                name="select_experience",
                payload={"experience": level},
                label=f"{info['emoji']} {level}"
            )
        )
    
    await cl.Message(
        content="👇 **Select your experience level:**",
        actions=actions
    ).send()


async def show_role_category_selection():
    """Display role category selection."""
    actions = []
    for category in ROLE_CATEGORIES.keys():
        emoji = "💻" if category == "Engineering" else "📊" if category == "Data & AI" else "🔧" if category == "Specialized" else "👔"
        actions.append(
            cl.Action(
                name="select_role_category",
                payload={"category": category},
                label=f"{emoji} {category}"
            )
        )
    
    await cl.Message(
        content="👇 **Select your role category:**",
        actions=actions
    ).send()


async def show_role_selection(category: str):
    """Display specific role selection based on category."""
    roles = ROLE_CATEGORIES.get(category, ROLE_CATEGORIES["Engineering"])
    actions = []
    for role in roles:
        actions.append(
            cl.Action(
                name="select_role",
                payload={"role": role},
                label=f"💼 {role}"
            )
        )
    
    await cl.Message(
        content=f"👇 **Select your specific role in {category}:**",
        actions=actions
    ).send()


async def show_question_count_selection():
    """Display question count selection."""
    options = [
        ("5", "⚡ Quick (5 questions)"),
        ("7", "📝 Standard (7 questions)"),
        ("10", "📚 Thorough (10 questions)"),
        ("12", "🎯 Comprehensive (12 questions)")
    ]
    
    actions = []
    for value, label in options:
        actions.append(
            cl.Action(
                name="select_questions",
                payload={"num_questions": value},
                label=label
            )
        )
    
    await cl.Message(
        content="👇 **How many questions would you like?**",
        actions=actions
    ).send()


async def show_settings_summary():
    """Display the final settings summary and prompt for resume upload."""
    settings = cl.user_session.get("interview_settings")
    company_info = COMPANY_PRESETS.get(settings["company"], COMPANY_PRESETS["Other Company"])
    exp_info = EXPERIENCE_LEVELS.get(settings["experience"], EXPERIENCE_LEVELS["Mid-Level (3-5 years)"])
    
    summary = f"""## ✅ Interview Setup Complete!

### Your Interview Configuration:

| Setting | Value |
|---------|-------|
| 🏢 **Company** | {company_info['emoji']} {settings['company']} |
| 💼 **Role** | {settings['role']} |
| 📈 **Level** | {exp_info['emoji']} {settings['experience']} |
| ❓ **Questions** | {settings['num_questions']} |

### Company Interview Style:
> *{company_info['style']}*

### Focus Areas for {settings['experience']}:
> *{exp_info['focus']}*

---

## 📄 Now upload your resume (PDF) to start!

Simply drag & drop your resume or click the 📎 attachment button below."""

    # Add a restart button
    actions = [
        cl.Action(
            name="restart_setup",
            payload={},
            label="🔄 Change Settings"
        )
    ]
    
    await cl.Message(content=summary, actions=actions).send()
    cl.user_session.set("state", "awaiting_resume")


@cl.action_callback("select_company")
async def on_company_select(action: cl.Action):
    """Handle company selection."""
    company = action.payload.get("company")
    settings = cl.user_session.get("interview_settings")
    settings["company"] = company
    cl.user_session.set("interview_settings", settings)
    
    company_info = COMPANY_PRESETS.get(company, COMPANY_PRESETS["Other Company"])
    
    await cl.Message(
        content=f"""✅ **Company Selected:** {company_info['emoji']} **{company}**

*Interview style: {company_info['style']}*

---

**Step 2 of 4:** What's your experience level?"""
    ).send()
    
    cl.user_session.set("state", "setup_experience")
    await show_experience_selection()


@cl.action_callback("select_experience")
async def on_experience_select(action: cl.Action):
    """Handle experience level selection."""
    experience = action.payload.get("experience")
    settings = cl.user_session.get("interview_settings")
    settings["experience"] = experience
    cl.user_session.set("interview_settings", settings)
    
    exp_info = EXPERIENCE_LEVELS.get(experience, EXPERIENCE_LEVELS["Mid-Level (3-5 years)"])
    
    await cl.Message(
        content=f"""✅ **Experience Level:** {exp_info['emoji']} **{experience}**

*Question difficulty: {exp_info['question_difficulty']}*

---

**Step 3 of 4:** What role are you applying for?"""
    ).send()
    
    cl.user_session.set("state", "setup_role_category")
    await show_role_category_selection()


@cl.action_callback("select_role_category")
async def on_role_category_select(action: cl.Action):
    """Handle role category selection."""
    category = action.payload.get("category")
    cl.user_session.set("current_role_category", category)
    
    await cl.Message(content=f"📂 **Category:** {category}").send()
    await show_role_selection(category)


@cl.action_callback("select_role")
async def on_role_select(action: cl.Action):
    """Handle role selection."""
    role = action.payload.get("role")
    settings = cl.user_session.get("interview_settings")
    settings["role"] = role
    cl.user_session.set("interview_settings", settings)
    
    await cl.Message(
        content=f"""✅ **Role Selected:** 💼 **{role}**

---

**Step 4 of 4:** How thorough should the interview be?"""
    ).send()
    
    cl.user_session.set("state", "setup_questions")
    await show_question_count_selection()


@cl.action_callback("select_questions")
async def on_questions_select(action: cl.Action):
    """Handle question count selection."""
    num_questions = int(action.payload.get("num_questions"))
    settings = cl.user_session.get("interview_settings")
    settings["num_questions"] = num_questions
    cl.user_session.set("interview_settings", settings)
    
    await cl.Message(content=f"✅ **Questions:** {num_questions}").send()
    await show_settings_summary()


@cl.action_callback("restart_setup")
async def on_restart_setup(action: cl.Action):
    """Restart the setup process."""
    cl.user_session.set("state", "setup_company")
    cl.user_session.set("interview_settings", {
        "company": None,
        "role": None,
        "experience": None,
        "num_questions": 7
    })
    
    await cl.Message(content="🔄 **Restarting setup...**\n\n**Step 1 of 4:** Which company are you preparing for?").send()
    await show_company_selection()


@cl.action_callback("start_new_interview")
async def on_start_new(action: cl.Action):
    """Start a completely new interview session."""
    await start()


@cl.action_callback("view_history")
async def on_view_history(action: cl.Action):
    """Show the user's past interview sessions."""
    username = _get_username()
    interviews = get_user_interviews(username, limit=10)

    if not interviews:
        await cl.Message(content="📜 You haven't completed any interviews yet. Start one now!").send()
        return

    rows = ""
    for iv in interviews:
        date_str = iv["created_at"][:10]
        rows += f"| {date_str} | {iv['company']} | {iv['role']} | {iv['experience_level']} | {iv['fit_score']}/100 | {iv['num_questions']} |\n"

    history_msg = f"""## 📜 Your Interview History (last {len(interviews)})

| Date | Company | Role | Level | Score | Questions |
|------|---------|------|-------|-------|-----------|
{rows}
---
*Start a new interview to keep improving!*"""

    actions = [
        cl.Action(name="start_new_interview", payload={}, label="🆕 Start New Interview")
    ]
    await cl.Message(content=history_msg, actions=actions).send()


@cl.on_message
async def main(message: cl.Message):
    """
    Handle incoming messages from users.
    """
    state = cl.user_session.get("state")
    
    # Stop any playing audio when user sends a message
    cl.user_session.set("stop_audio", True)
    
    # Check if resume was uploaded with the message
    if message.elements:
        for element in message.elements:
            if hasattr(element, 'mime') and element.mime == "application/pdf":
                # Check if setup is complete
                settings = cl.user_session.get("interview_settings", {})
                if not settings.get("company") or not settings.get("role") or not settings.get("experience"):
                    await cl.Message(
                        content="⚠️ Please complete the interview setup first by selecting company, role, and experience level."
                    ).send()
                    await show_company_selection()
                    return
                await handle_file_upload(message.elements)
                return
    
    # Handle text/audio messages in interview mode
    if state == "interview":
        user_input = message.content
        
        if not user_input or not user_input.strip():
            await cl.Message(content="💬 Please provide a response (voice or text).").send()
            return
        
        await handle_interview_response(user_input)
        return
    
    # Handle messages during setup phases
    if state and state.startswith("setup_"):
        await cl.Message(
            content="👆 Please use the buttons above to make your selection."
        ).send()
        return
    
    if state == "awaiting_resume":
        await cl.Message(
            content="📄 Please upload your resume (PDF file) to start the interview.\n\nYou can drag & drop the file or click the 📎 button below."
        ).send()
    elif state == "rejected":
        actions = [
            cl.Action(name="restart_setup", payload={}, label="🔄 Try Different Settings"),
            cl.Action(name="start_new_interview", payload={}, label="🆕 Start Over")
        ]
        await cl.Message(
            content="Your profile didn't meet the threshold for this configuration. You can try with different settings or upload a different resume.",
            actions=actions
        ).send()
    elif state == "completed":
        actions = [
            cl.Action(name="start_new_interview", payload={}, label="🆕 Start New Interview"),
            cl.Action(name="view_history", payload={}, label="📜 View Interview History"),
        ]
        await cl.Message(
            content="🎉 Your interview is complete! Click below to start a new practice session or view your history.",
            actions=actions
        ).send()
    else:
        await cl.Message(
            content="Welcome! Please wait while I set up your interview session..."
        ).send()
        await start()


async def handle_interview_response(user_input: str):
    """
    Handle candidate responses during the interview.
    """
    interviewer = cl.user_session.get("interviewer")
    
    if not interviewer:
        await cl.Message(content="⚠️ Interview session not initialized. Please restart.").send()
        actions = [cl.Action(name="start_new_interview", payload={}, label="🆕 Start New Interview")]
        await cl.Message(content="Click below to start fresh:", actions=actions).send()
        return
    
    # Reset audio stop flag
    cl.user_session.set("stop_audio", False)
    
    # Store the user's response in conversation history first
    interviewer.add_candidate_response(user_input)
    
    # Show progress indicator
    progress = f"📊 Progress: Question {interviewer.responses_received} of {interviewer.max_questions} answered"
    
    # Check if interview should conclude AFTER receiving this response
    if interviewer.should_conclude_interview():
        await cl.Message(content=f"{progress} ✅").send()
        
        # Generate and save summary
        async with cl.Step(name="📝 Generating Your Feedback Report", type="tool") as step:
            step.output = "Analyzing your responses and creating personalized feedback..."
            summary = interviewer.generate_summary()
            
            # Save to file
            report_saved = interviewer.save_interview_report(summary)
            if report_saved:
                step.output = "✓ Report generated and saved!"
            else:
                step.output = "✓ Report generated!"
        
        # Get interview settings for the final message
        settings = cl.user_session.get("interview_settings", {})
        company = settings.get("company", "Other Company")
        company_info = COMPANY_PRESETS.get(company, COMPANY_PRESETS["Other Company"])
        
        # Send conclusion message
        conclusion = f"""# 🎉 Interview Complete!

Thank you for completing this mock interview for **{company_info['emoji']} {company}**!

---

## 📊 Your Performance Report

{summary}

---

{'📁 *A detailed report has been saved to `interview_report.txt`*' if report_saved else ''}

### What's Next?
- Review the feedback above carefully
- Practice the areas marked for improvement
- Try another interview with different settings!"""

        actions = [
            cl.Action(name="start_new_interview", payload={}, label="🆕 Start New Interview"),
            cl.Action(name="restart_setup", payload={}, label="🔄 Try Different Company")
        ]
        
        # Create audio feedback message (shorter version for TTS)
        audio_feedback = f"Congratulations! You have completed the mock interview for {company}. " \
                        f"I have analyzed your responses and generated a detailed performance report. " \
                        f"Please review the feedback on screen carefully. It includes your strengths, " \
                        f"areas for improvement, and specific recommendations to help you succeed in your actual interview. " \
                        f"Good luck with your preparation!"
        
        # Send conclusion with voice
        await send_voice_message_with_content(audio_feedback, conclusion, actions)

        # Persist the interview to history
        username = _get_username()
        candidate_data = cl.user_session.get("candidate_data") or {}
        save_interview(
            username=username,
            company=company,
            role=settings.get("role", "Software Engineer"),
            experience_level=settings.get("experience", "Mid-Level (3-5 years)"),
            fit_score=candidate_data.get("fit_score", 0),
            num_questions=interviewer.max_questions,
            summary=summary,
            transcript=interviewer.conversation_history,
        )

        # Update state
        cl.user_session.set("state", "completed")
    else:
        # Generate interviewer's response/next question
        async with cl.Step(name="🤔 Preparing Next Question", type="tool") as step:
            interviewer_response = interviewer.generate_question()
            step.output = f"Question {interviewer.questions_asked} of {interviewer.max_questions}"
        
        # Show progress
        remaining = interviewer.max_questions - interviewer.responses_received
        await cl.Message(content=f"*{progress} | {remaining} remaining*").send()
        
        # Continue interview - send next question
        await send_voice_message(interviewer_response)


async def send_voice_message(text: str):
    """
    Send a message with text and auto-playing audio for the AI interviewer.
    
    Args:
        text: Message text to send
    """
    try:
        # Reset stop flag
        cl.user_session.set("stop_audio", False)
        
        # Generate audio for TTS
        audio_path = text_to_speech(text)
        
        if audio_path and os.path.exists(audio_path):
            # Send message with auto-playing audio
            audio_element = cl.Audio(
                name="interviewer_voice",
                path=audio_path,
                display="inline",
                auto_play=True
            )
            await cl.Message(
                content=f"🎤 **Interviewer:**\n\n{text}",
                elements=[audio_element]
            ).send()
        else:
            # Fallback to text only if audio generation fails
            await cl.Message(content=f"🎤 **Interviewer:**\n\n{text}").send()
            
    except Exception as e:
        print(f"Error sending voice message: {str(e)}")
        await cl.Message(content=f"🎤 **Interviewer:**\n\n{text}").send()


async def send_voice_message_with_content(audio_text: str, display_content: str, actions: list = None):
    """
    Send a message with custom display content and separate audio text.
    Useful for feedback where we want detailed text but shorter audio.
    
    Args:
        audio_text: Text to convert to speech (shorter version)
        display_content: Full content to display in the message
        actions: Optional list of action buttons
    """
    try:
        # Reset stop flag
        cl.user_session.set("stop_audio", False)
        
        # Generate audio for TTS
        audio_path = text_to_speech(audio_text)
        
        if audio_path and os.path.exists(audio_path):
            # Send message with auto-playing audio
            audio_element = cl.Audio(
                name="feedback_voice",
                path=audio_path,
                display="inline",
                auto_play=True
            )
            await cl.Message(
                content=display_content,
                elements=[audio_element],
                actions=actions
            ).send()
        else:
            # Fallback to text only if audio generation fails
            await cl.Message(content=display_content, actions=actions).send()
            
    except Exception as e:
        print(f"Error sending voice message with content: {str(e)}")
        await cl.Message(content=display_content, actions=actions).send()


async def handle_file_upload(elements):
    """
    Handle file uploads and trigger autonomous evaluation."""
    # Get interview settings
    settings = cl.user_session.get("interview_settings", {})
    interview_settings = {
        "company": settings.get("company", "Other Company"),
        "role": settings.get("role", "Software Engineer"),
        "experience": settings.get("experience", "Mid-Level (3-5 years)"),
        "num_questions": settings.get("num_questions", 7)
    }
    
    for element in elements:
        if isinstance(element, cl.File):
            # Only process PDF files
            if not element.name.lower().endswith('.pdf'):
                await cl.Message(
                    content="❌ **Invalid file format.** Please upload a PDF file."
                ).send()
                return
            
            await cl.Message(content="📄 **Resume received!** Analyzing your profile...").send()
            
            # Step 1: Reading Resume
            async with cl.Step(name="📖 Reading Resume", type="tool") as step:
                step.output = "Extracting content from PDF..."
                resume_text = extract_text(element.path)
                
                if not resume_text:
                    await cl.Message(
                        content="❌ **Could not read the PDF.** Please ensure it's a valid, text-based PDF (not scanned image)."
                    ).send()
                    return
                
                step.output = f"✓ Extracted {len(resume_text)} characters"
            
            # Step 2: Analyzing Profile
            company_info = COMPANY_PRESETS.get(interview_settings['company'], COMPANY_PRESETS["Other Company"])
            async with cl.Step(name="🔍 Analyzing Profile", type="tool") as step:
                step.output = f"Evaluating fit for {interview_settings['role']} at {interview_settings['company']}..."
                
                evaluation_data = evaluate_candidate(
                    resume_text, 
                    job_description=interview_settings['role'],
                    company=interview_settings['company'],
                    experience_level=interview_settings['experience']
                )
                
                if not evaluation_data:
                    await cl.Message(
                        content="❌ **Analysis failed.** Please try again or check your resume format."
                    ).send()
                    return
                
                cl.user_session.set("candidate_data", evaluation_data)
                step.output = f"✓ Profile analyzed: Score {evaluation_data.get('fit_score', 0)}/100"
            
            # Display evaluation summary
            summary = format_evaluation_summary(evaluation_data, interview_settings)
            await cl.Message(content=summary).send()
            
            # Step 3: Decision
            fit_score = evaluation_data.get('fit_score', 0)
            threshold = 50  # Lower threshold for practice - everyone should be able to practice
            
            async with cl.Step(name="🎯 Preparing Interview", type="tool") as step:
                if fit_score >= threshold:
                    step.output = "✓ Ready to start interview!"
                    cl.user_session.set("state", "interview")
                    
                    # Initialize interview agent
                    interviewer = InterviewAgent(
                        candidate_data=evaluation_data,
                        company=interview_settings['company'],
                        experience_level=interview_settings['experience'],
                        max_questions=interview_settings['num_questions']
                    )
                    cl.user_session.set("interviewer", interviewer)
                    
                    # Start message
                    start_msg = f"""## 🎬 Let's Begin Your Mock Interview!

**Candidate:** {evaluation_data.get('name', 'Candidate')}
**Company:** {company_info['emoji']} {interview_settings['company']}
**Role:** {interview_settings['role']}
**Level:** {interview_settings['experience']}

---

### 📋 Interview Format:
- {interview_settings['num_questions']} questions total
- Mix of technical & behavioral questions
- {company_info['style']}

### 💡 Tips:
- Take a moment to think before answering
- Be specific with examples from your experience
- You can respond via **voice 🎤** or **text ⌨️**

---

*Starting interview...*"""
                    
                    await cl.Message(content=start_msg).send()
                    
                    # Generate and send first question
                    first_question = interviewer.generate_question()
                    await send_voice_message(first_question)
                    
                else:
                    step.output = "Profile needs improvement for this role"
                    cl.user_session.set("state", "rejected")
                    
                    actions = [
                        cl.Action(name="restart_setup", payload={}, label="🔄 Try Different Settings"),
                        cl.Action(name="start_new_interview", payload={}, label="🆕 Start Over")
                    ]
                    
                    await cl.Message(
                        content=f"""### 📊 Profile Assessment

Your current score of **{fit_score}/100** suggests some areas for improvement before interviewing for **{interview_settings['role']}** at **{interview_settings['company']}**.

**Recommendations:**
1. Focus on skills commonly required at {interview_settings['company']}
2. Add relevant projects to your portfolio
3. Consider trying a different experience level or role

You can adjust settings and try again!""",
                        actions=actions
                    ).send()
            
            return


if __name__ == "__main__":
    # This allows the app to be run directly, though Chainlit should be used via CLI
    print("Please run this app using: chainlit run app.py")
