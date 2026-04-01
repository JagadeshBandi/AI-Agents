# CareerNavigator AI

Your AI-powered assistant for UK and USA job hunting, CV optimization, LinkedIn enhancement, and career advancement. Get ATS-friendly CV analysis, job description matching, recruiter connection strategies, and freelancing guidance.

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd AI-Agents

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy the environment file
cp .env.example .env

# Edit .env with your API keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
HUGGINGFACE_TOKEN=your_huggingface_token_here
```

### 3. Run the Application

**Start CareerNavigator AI**
```bash
python app.py
```

**Access the Career Dashboard**
- Open browser to http://localhost:8000
- Navigate to CareerNavigator interface

**Alternative Streamlit Interface**
```bash
streamlit run streamlit_app.py
```

### 4. Access CareerNavigator

- **CareerNavigator Dashboard**: http://localhost:8000/career
- **CV Analyzer**: Analyze and optimize your CV for ATS systems
- **Job Matcher**: Match your CV against job descriptions
- **LinkedIn Optimizer**: Enhance your LinkedIn profile
- **Job Search Strategy**: Get market-specific job hunting guidance
- **Recruiter Connection**: Learn how to connect with recruiters
- **Freelancing Guide**: Platform recommendations and strategies

The system provides instant analysis and actionable recommendations for your career advancement.

## Project Structure

```
AI-Agents/
├── src/                      # Source code
│   ├── career_navigator.py  # CareerNavigator AI core system
│   ├── agent.py             # Core AI agent classes
│   ├── api.py               # Basic FastAPI web server
│   ├── advanced_api.py      # Advanced API with automation
│   ├── automation.py        # Advanced automation engine
│   ├── config.py            # Configuration management
│   ├── llm_providers.py     # LLM provider implementations
│   └── training.py          # Model training and fine-tuning
├── templates/               # HTML templates
│   ├── career_navigator.html # CareerNavigator web interface
│   └── chat.html            # Web chat interface
├── static/                  # Static assets
├── data/                    # Training and conversation data
├── models/                  # Trained models
├── app.py                   # Main automated web application
├── main.py                  # Alternative entry point
├── streamlit_app.py         # Streamlit interface
├── requirements.txt         # Python dependencies
└── .env.example            # Environment variables template

```

## CareerNavigator Usage

### CV Analysis Example

1. Navigate to CV Analyzer tab
2. Select target country (UK or USA)
3. Enter target role
4. Paste your CV content
5. Click "Analyze CV"
6. Review detailed scores and recommendations

### Job Matching Example

1. Go to Job Matcher tab
2. Paste your CV in left panel
3. Paste job description in right panel
4. Click "Calculate Match Score"
5. Review match percentage and missing keywords
6. Apply recommendations to improve match

### LinkedIn Optimization

1. Open LinkedIn Optimizer tab
2. Enter your headline, summary, and skills
3. Select target country
4. Click "Optimize Profile"
5. Implement suggested improvements

### Recruiter Connection Strategy

1. Select Recruiters tab
2. Choose your industry and target country
3. Get personalized connection strategies
4. Use provided message templates
5. Follow dos and don'ts guidelines


## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

If you have questions or need help:

1. Check the documentation
2. Search existing issues
3. Create a new issue with details
4. Join our community discussions

---

**Built with care for the AI community**