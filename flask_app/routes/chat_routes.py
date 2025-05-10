from flask import Flask, Blueprint, request, jsonify
import logging
import os
from dotenv import load_dotenv

import json
from pydantic import BaseModel
import openai
from typing import List

from extensions import limiter

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

ai_client = openai.OpenAI()

chat_bp = Blueprint('chat', __name__)

# OpenAI Connection 
openai.api_key = os.getenv('OPENAI_API_KEY')
if not openai.api_key:
    logger.error('OpenAI Api Key not found')


@chat_bp.route('/api/chat', methods = ['POST'])
@limiter.limit("50 per day")
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        chat_history = data.get('chatHistory', [])

        # Input Validation 
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Conversation history
        messages = []
        
        # Add chat history if available 
        if chat_history:
            for msg in chat_history:
                role = "user" if msg.get('sender') == 'user' else 'assistant'
                messages.append({'role': role, "content": msg.get('text', '')})

        # Add a new user message
        messages.append({'role': 'user', 'content': user_message})

        messages.append({
            "role": "system",
            "content": "You are an expert at structured data extraction. "
            "You task will be to search for books that specify user criteria for each of the following countries: "
            "Ukraine, Italy, Germany and return them in a specified Json Structure. Make sure you do not invent any "
            "information and give me true goodreads link along with true rating extracted from goodreads. "
            "Here is an example output:"
            """{'country_id': 'France',
             'title': 'Les Misérables',
            'author': 'Victor Hugo',
            'year': 1862,
            'rating': 4.4,
            'goodreads_url': 'https://www.goodreads.com/book/show/24280.Les_Mis_rables'
            },
            {
            'country_id': 'Russia',
            'title': 'The Master and Margarita',
            'author': 'Mikhail Bulgakov',
            'year': 1967,
            'rating': 4.3,
            'goodreads_url': 'https://www.goodreads.com/book/show/117833.The_Master_and_Margarita'
            }
            """
        })

        # Call OpenAI Api
        logger.info(f'Sending request to OpenAI with {len(messages)} messages')

        class CountriesBooksExtraction(BaseModel):
            country_id: str
            title: str
            author: str
            year: int
            rating: int
            goodreads_url: str
        
        class ListCountriesBooksExtraction(BaseModel):
             countries: List[CountriesBooksExtraction]

        response = ai_client.responses.parse(
            model="gpt-4o-2024-08-06",
            input = messages,
            text_format=ListCountriesBooksExtraction
        )

        bot_response_dict = response.output_parsed.model_dump()
        bot_response_json = json.dumps(bot_response_dict)

        response_for_user = []
        response_for_user.append({'role': 'system', 'content': f'Summarise the gist of books provided in a following JSON with 3 sentences maximum. For example: These books talk about adventures that friends pursue together.The challenges they face and how they overcome them: {bot_response_json}'})

        response_summary =  ai_client.responses.create(
            model="gpt-4o-2024-08-06",
            input = response_for_user
        )

        return jsonify({'json_response': bot_response_json, 
                        'response_summary': response_summary.output_text})
    
    except openai.APIError as e:
            logger.error(f"OpenAI API Error: {str(e)}")
            return jsonify({"error": "Error communicating with OpenAI API"}), 500
    except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return jsonify({"error": "An unexpected error occurred"}), 500
