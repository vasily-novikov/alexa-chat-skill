# Alexa Chat Skill for Ivan

A friendly German-language Alexa chat bot skill powered by OpenAI for conversational practice.

## Features
- Conversational AI responses using OpenAI API
- German male voice (Hans)
- Maintains conversation context (last 6 turns)
- Cost-optimized with token limits and text trimming

## Setup

1. Set environment variable: `OPENAI_API_KEY`
2. Deploy to AWS Lambda
3. Configure in Alexa Developer Console

## Dependencies
- ask-sdk-core
- requests

Install with:
```bash
pip install ask-sdk-core requests
```

## Configuration
- Model: o4-mini
- Max input: 1500 characters
- Max output: 80 tokens
