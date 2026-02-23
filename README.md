# 🎙️ Virtual Interview Preparation AI Agent

An intelligent AI-powered interview preparation system that helps candidates practice for interviews at top tech companies. Built for the DECTHON 2026 Hackathon.

## 🌟 Key Features

### Company-Specific Interview Preparation
- **Google** - Problem-solving, Algorithms, System Design, STAR behavioral questions
- **Amazon** - Leadership Principles focused, Customer obsession, Ownership
- **Microsoft** - Growth Mindset, Technical Depth, Collaboration
- **Meta** - Move Fast, Scale Thinking, Impact Focus
- **Apple** - Design Thinking, Attention to Detail, Quality Focus
- **Netflix** - High Performance Culture, Freedom and Responsibility
- **Startup** - Versatility, Adaptability, Full-Stack Thinking
- **General** - Standard Technical Interview

### Experience Level Matching
- **Fresher (0-1 years)** - Basic concepts, Learning potential, Academic projects
- **Junior (1-3 years)** - Practical experience, Code quality, Teamwork
- **Mid-Level (3-5 years)** - System design basics, Leadership potential
- **Senior (5-8 years)** - Architecture, Technical leadership, Strategy
- **Lead/Staff (8+ years)** - System architecture, Organizational impact

### Technical Features
- ✅ **Resume Analysis** - AI-powered analysis of qualifications
- ✅ **Dynamic Role Selection** - 20+ common tech roles supported
- ✅ **Voice & Text Input** - Respond using voice or keyboard
- ✅ **Customizable Interview Length** - 5 to 15 questions
- ✅ **Detailed Feedback** - Company-specific improvement suggestions
- ✅ **Interview Reports** - Comprehensive summaries saved to file
- ✅ **User Authentication** - Login / sign-up with secure password hashing
- ✅ **Interview History** - Track past interviews, scores, and progress over time
- ✅ **Personal Dashboard** - View stats (total interviews, average score, best score)

## 🛠️ Tech Stack

- **UI Framework**: Chainlit (chat and audio capabilities)
- **AI Framework**: LangChain
- **AI Models**: 
  - GPT-4o (evaluation and interview logic)
  - Whisper (speech-to-text)
  - OpenAI TTS (text-to-speech)
- **PDF Processing**: pypdf
- **Authentication**: bcrypt password hashing, Chainlit auth
- **Data Storage**: SQLite (user accounts & interview history)
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
git clone https://github.com/Kumarmanish4444333221/Virtual-Interview-Prepration-AI-Agent.git
cd Virtual-Interview-Prepration-AI-Agent
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

2. Edit `.env` and add your keys:
   ```
   OPENAI_API_KEY=sk-your-api-key-here
   CHAINLIT_AUTH_SECRET=any-random-secret-string
   ```

### 5. Run the Application

```bash
chainlit run app.py
```

The application will start and open in your default browser at `http://localhost:8000`

## 📖 How to Use

### Step 1: Configure Interview Settings
1. Open the application in your browser
2. Use the sidebar settings to select:
   - **Target Company** (Google, Amazon, Microsoft, etc.)
   - **Target Role** (Software Engineer, Data Scientist, etc.)
   - **Experience Level** (Fresher to Lead/Staff)
   - **Number of Questions** (5-15)

### Step 2: Upload Resume
Upload your resume in PDF format. The AI will analyze your qualifications.

### Step 3: Take the Interview
- Answer questions using **voice** 🎤 or **text** ⌨️
- Take your time to think before answering
- Be specific with examples from your experience

### Step 4: Get Feedback
Receive comprehensive feedback including:
- Technical competency rating
- Communication skills assessment
- Company culture fit analysis
- Specific preparation tips for your target company
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
│   ├── interviewer.py         # Interview logic & conversation
│   ├── auth.py                # User authentication (login/signup)
│   └── history.py             # Interview history persistence
├── tests/
│   ├── test_auth.py           # Auth module tests
│   └── test_history.py        # History module tests
├── data/                      # SQLite databases (auto-created, git-ignored)
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

- All API keys and secrets are stored in `.env` (git-ignored)
- User passwords are hashed with **bcrypt** before storage
- Authentication tokens are signed with a configurable secret (`CHAINLIT_AUTH_SECRET`)
- Interview history is stored locally in SQLite (inside `data/`, git-ignored)
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