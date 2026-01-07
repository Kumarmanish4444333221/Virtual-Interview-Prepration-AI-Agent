# 🎙️ Autonomous Recruitment & Interview Agent

An intelligent, autonomous AI-powered recruitment system that evaluates candidates and conducts voice interviews with minimal human intervention. Built for the DECTHON 2026 Hackathon.

## 🌟 Key Features

### Autonomous Behaviors
1. **Goal Understanding** - Automatically understands recruitment objectives from resume uploads
2. **Task Decomposition** - Breaks down the process into clear steps (PDF parsing → evaluation → decision → interview → reporting)
3. **Decision Making** - Autonomously decides to interview or reject candidates based on fit score (threshold: 75/100)
4. **Tool Usage** - Intelligently uses Whisper STT, GPT-4o for evaluation/interview, and OpenAI TTS for voice
5. **End-to-End Completion** - Generates comprehensive interview reports without human guidance

### Technical Features
- ✅ **Resume Analysis** - Extracts and analyzes candidate qualifications from PDF resumes
- ✅ **AI-Powered Evaluation** - Uses GPT-4o to evaluate candidates and calculate fit scores
- ✅ **Voice Interview** - Conducts natural conversational interviews with speech-to-text and text-to-speech
- ✅ **Autonomous Decision Making** - Automatically progresses qualified candidates to interviews
- ✅ **Interview Reports** - Generates and saves comprehensive interview summaries
- ✅ **Real-time Reasoning Display** - Shows AI decision-making process using visual steps

## 🛠️ Tech Stack

- **UI Framework**: Chainlit (chat and audio capabilities)
- **AI Framework**: LangChain
- **AI Models**: 
  - GPT-4o (evaluation and interview logic)
  - Whisper (speech-to-text)
  - OpenAI TTS (text-to-speech)
- **PDF Processing**: pypdf
- **Environment**: Python 3.8+, Windows compatible

## 📋 Prerequisites

- Python 3.8 or higher
- OpenAI API key with access to:
  - GPT-4o
  - Whisper
  - TTS

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Kumarmanish4444333221/Interview-Preparation-or-Recruitor-AI-Agent.git
cd Interview-Preparation-or-Recruitor-AI-Agent
```

### 2. Create Virtual Environment (Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

1. Copy the `.env.example` file to `.env`:
   ```bash
   copy .env.example .env    # Windows
   cp .env.example .env      # macOS/Linux
   ```

2. Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-your-api-key-here
   ```

### 5. Run the Application

```bash
chainlit run app.py
```

The application will start and open in your default browser at `http://localhost:8000`

## 📖 How to Use

### Step 1: Upload Resume
1. Open the application in your browser
2. Upload a candidate's resume in PDF format
3. The agent will automatically extract and analyze the resume

### Step 2: Autonomous Evaluation
The agent will autonomously:
- Extract text from the PDF
- Analyze skills, experience, and qualifications
- Calculate a fit score (0-100)
- Make a decision:
  - **Score ≥ 75**: Proceed to interview
  - **Score < 75**: Provide feedback and reject

### Step 3: Voice Interview (If Qualified)
For qualified candidates:
- The agent conducts a conversational voice interview
- You can respond via voice (click microphone) or text
- The agent asks 5 relevant technical questions
- All responses are transcribed and analyzed

### Step 4: Interview Report
After completing the interview:
- A comprehensive summary is generated automatically
- The report is saved to `interview_report.txt`
- Includes: transcript, assessment, strengths, recommendations

## 🏗️ Project Structure

```
├── app.py                      # Main Chainlit application
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .chainlit/
│   └── config.toml            # Chainlit configuration
├── modules/
│   ├── __init__.py
│   ├── pdf_processor.py       # PDF text extraction
│   ├── evaluator.py           # LangChain candidate evaluation
│   ├── audio_handler.py       # Whisper STT & OpenAI TTS
│   └── interviewer.py         # Interview logic & conversation
└── README.md                  # This file
```

## 🎯 Autonomous Decision Flow

```
Resume Upload
    ↓
[🧠 Reading Resume] - Extract text from PDF
    ↓
[🤔 Analyzing Skills] - Evaluate with GPT-4o
    ↓
[📊 Calculating Score] - Generate fit score (0-100)
    ↓
[🎯 Making Decision] - Autonomous threshold check
    ↓
    ├─→ Score ≥ 75: ✅ Start Interview
    │       ↓
    │   [🎙️ Conduct Interview] - 5 questions with voice
    │       ↓
    │   [📝 Generate Report] - Comprehensive summary
    │       ↓
    │   [💾 Save Report] - interview_report.txt
    │
    └─→ Score < 75: ❌ Provide Feedback & Reject
```

## 🔧 Configuration

### Chainlit Settings
Edit `.chainlit/config.toml` to customize:
- Audio recording settings
- File upload restrictions
- UI theme and appearance
- Session timeout

### Interview Settings
Edit `modules/interviewer.py` to customize:
- Number of interview questions (`max_questions`)
- Interview tone and style
- Evaluation criteria

## 🐛 Troubleshooting

### Common Issues

**1. "OPENAI_API_KEY not found"**
- Ensure `.env` file exists in the project root
- Verify the API key is correctly formatted
- Check that the key has necessary permissions

**2. PDF extraction fails**
- Ensure the PDF is not password-protected
- Verify the PDF contains extractable text (not scanned images)
- Try a different PDF file

**3. Audio not working**
- Check microphone permissions in your browser
- Ensure you're using HTTPS or localhost
- Try using text input as an alternative

**4. Module import errors**
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check that you're using the correct Python version (3.8+)

## 💡 Tips for Best Results

1. **Resume Quality**: Upload resumes with clear formatting and extractable text
2. **Audio Input**: Speak clearly when using voice responses
3. **Network**: Ensure stable internet connection for API calls
4. **API Usage**: Monitor OpenAI API usage to manage costs

## 🔒 Security & Privacy

- All API keys are stored in `.env` (git-ignored)
- No candidate data is stored permanently (except interview reports)
- Audio files are temporarily stored and can be cleared
- Interview reports are saved locally and not shared

## 📊 Features Demonstrated for DECTHON 2026

✅ **Autonomous Behavior**
- Goal understanding from resume upload
- Self-directed task decomposition
- Independent decision-making based on evaluation
- Proactive interview conclusion and reporting

✅ **Tool Integration**
- OpenAI GPT-4o for reasoning and evaluation
- Whisper for speech recognition
- TTS for natural voice responses
- LangChain for structured AI workflows

✅ **End-to-End Workflow**
- Complete recruitment pipeline
- No manual intervention required
- Comprehensive output (interview report)

✅ **Professional UI**
- Clean Chainlit interface
- Visual reasoning steps (cl.Step)
- Audio/voice support
- Real-time feedback

## 📝 License

This project is created for the DECTHON 2026 Hackathon.

## 🤝 Contributing

This is a hackathon project. For suggestions or issues, please open a GitHub issue.

## 📧 Contact

For questions about this project, please reach out through GitHub issues.

---

**Built with ❤️ for DECTHON 2026 Hackathon**