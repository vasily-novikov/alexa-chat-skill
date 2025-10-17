# Alexa Chat Skill for Ivan

A friendly German-language Alexa chat bot skill powered by OpenAI for conversational practice.

## Features
- Conversational AI responses using OpenAI API
- German male voice (Hans)
- Maintains conversation context (last 6 turns)
- Cost-optimized with token limits and text trimming

## Structure
```
alexa-chat-skill/
├── lambda/
│   ├── lambda_function.py    # Main skill code
│   └── requirements.txt       # Python dependencies
└── skill-package/
    ├── interactionModels/
    │   └── custom/
    │       └── de-DE.json     # German interaction model
    └── skill.json             # Skill manifest
```

## Setup

### 1. Deploy Lambda Function
1. Zip the contents of the `lambda/` directory
2. Create an AWS Lambda function (Python 3.9+)
3. Upload the zip file
4. Set environment variable: `OPENAI_API_KEY`
5. Copy the Lambda ARN

### 2. Configure Alexa Skill
1. Go to [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask)
2. Create a new skill or import this package
3. Set the Lambda endpoint ARN in `skill-package/skill.json`
4. Build and test

## Dependencies
- ask-sdk-core>=1.11.0
- requests>=2.28.0

## Configuration
- Model: o4-mini
- Max input: 1500 characters
- Max output: 80 tokens
- Invocation name: "chat kumpel"
