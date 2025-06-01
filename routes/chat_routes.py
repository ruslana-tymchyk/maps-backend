from flask import Flask, Blueprint, request, jsonify
import logging
import os
from dotenv import load_dotenv
import urllib.parse

import json
from pydantic import BaseModel, computed_field
import openai
from typing import List

from flask_app.extensions import limiter

from data.countries import all_countries

import asyncio
import aiohttp

import inspect


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

async def chat(countries: list, user_message: str):
    try:
        data = request.json
        chat_history = data.get('chatHistory', [])
        # Conversation history
        messages = []
        
        # Add chat history if available 
        if chat_history:
            for msg in chat_history:
                role = "user" if msg.get('sender') == 'user' else 'assistant'
                messages.append({'role': role, "content": msg.get('text', '')})

        # Add a new user message
        messages.append({'role': 'user', 'content': user_message})

        example_output = [
            {
                'country_id': 'France',
                'title': 'Les Misérables',
                'author': 'Victor Hugo',
                'year': 1862,
                'rating': 4.4,
                'book_summary': "Les Misérables by Victor Hugo is a sweeping epic that follows ex-convict Jean Valjean’s quest for redemption while being relentlessly pursued by the righteous Inspector Javert. Set against the backdrop of 19th-century France, the novel explores themes of justice, poverty, love, and revolution through a cast of vivid characters. Its emotional depth and social criticism have made it a timeless classic of humanitarian literature."
            },
            {
                'country_id': 'Russia',
                'title': 'The Master and Margarita',
                'author': 'Mikhail Bulgakov',
                'year': 1967,
                'rating': 4.3,
                'book_summary': "The Master and Margarita by Mikhail Bulgakov is a surreal, satirical novel in which the Devil, disguised as Woland, arrives in 1930s Moscow to expose the hypocrisy of Soviet society. Interwoven are a love story between a tormented writer and his devoted Margarita, and a philosophical retelling of Jesus' trial by Pontius Pilate. Blending political satire, romance, and metaphysical themes, the novel is celebrated as a bold critique of censorship and a triumph of artistic imagination."
            }
        ]

        messages.append({
            "role": "system",
            "content": (
                "You are an expert at structured data extraction. "
                "Your task is to search for books that specify user criteria for each of the following countries: "
                f"{', '.join(countries)} and return them in a specified JSON structure. "
                "Make sure you do not invent any information and give the TRUE rating that actually corresponds to"
                "to a book rating extracted from Goodreads. Make sure you correctly identify year and name of the country."
                f"Make sure the book summary explains how this books is an example of book for the following user query: {user_message}"
                f"Here is an example output:\n{example_output}"
            )
        })


        # Call OpenAI Api
        logger.info(f'Sending request to OpenAI with {len(messages)} messages')

        class CountriesBooksExtraction(BaseModel):
            country_id: str
            title: str
            author: str
            year: int
            rating: int
            book_summary: str

            @computed_field
            @property 
            def google_url(self) -> str:
                """Generate a custom Google search URL for the book."""
                # Create search query: "book title" + author + goodreads
                search_query = f'"{self.title}" {self.author}'
                # URL encode the search query
                encoded_query = urllib.parse.quote_plus(search_query)
                return f"https://www.google.com/search?q={encoded_query}"
        
        class ListCountriesBooksExtraction(BaseModel):
             countries: List[CountriesBooksExtraction]

        return await asyncio.to_thread(
            ai_client.responses.parse,
            model="gpt-4o-2024-08-06",
            input = messages,
            text_format=ListCountriesBooksExtraction
        )
        
    
    except openai.APIError as e:
            logger.error(f"OpenAI API Error: {str(e)}")
            return jsonify({"error": "Error communicating with OpenAI API"}), 500
    except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return jsonify({"error": "An unexpected error occurred"}), 500

async def execute_concurrent_calls(all_countries: list):
    list_size = 30
    countries_lists = [all_countries[i: i+list_size] for i in range(0, len(all_countries), list_size)]


    data = request.json
    user_message = data.get('message', '')

    # Input Validation 
    if not user_message:
        return jsonify({'error': 'Message is required'}), 400
        

    # Launch concurrent calls
    results = await asyncio.gather(*[
        chat(list_chunk, user_message) for list_chunk in countries_lists
    ])

    response = [
         item.output_parsed.model_dump()
         for item in results
    ]

    # Merge all countries
    merged_countries = []
    for item in response:
        merged_countries.extend(item.get("countries", []))

    # Build the final structure
    merged_result = {"countries": merged_countries}

    # Convert to JSON string if needed
    bot_response_json = json.dumps(merged_result, indent=2)
    
    print(bot_response_json)

    response_for_user = []
    response_for_user.append({'role': 'system', 
                              'content': f'An LLM Literary Advisor is an expert at structured data extraction and it displays books based on user criteria on a map. This LLM Literary Advisor was asked to generate books based on user query {user_message}. YOUR TASK is to give a friendly response after user asked for a {user_message}, as if it was coming from LLM Literary Advisor that generated the output. DO NOT give examples of any book entries. Just say something SIMILAR TO (but change the phrasing to make it sound more natural): See the examples of "{user_message}" on a Map and in Entries Tab. Make sure you mention Map and Entries Tab, as this is part of UI that user will see.'})

    response_summary =  ai_client.responses.create(
        model="gpt-4o-2024-08-06",
        input = response_for_user
    )

    return jsonify({'json_response': bot_response_json, 
                    'response_summary': response_summary.output_text})



@chat_bp.route('/api/chat', methods = ['POST'])
@limiter.limit("50 per day")
def response_for_selected_countries():
     return(asyncio.run(execute_concurrent_calls(all_countries)))

@chat_bp.route('/')
def health():
    return {"status": "healthy"}