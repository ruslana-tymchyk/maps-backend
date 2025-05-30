from flask import Flask, Blueprint, request, jsonify
import logging
import os
from dotenv import load_dotenv

import json
from pydantic import BaseModel
import openai
from typing import List

from extensions import limiter

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

# It is a sync function
print(inspect.iscoroutinefunction(ai_client.responses.parse))

chat_bp = Blueprint('chat', __name__)

# OpenAI Connection 
openai.api_key = os.getenv('OPENAI_API_KEY')
if not openai.api_key:
    logger.error('OpenAI Api Key not found')

async def chat(countries: list):
    print('---------------------------------------------')
    print('-------YOU CALLED ME-------------------------')
    print('---------------------------------------------')
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

        example_output = [
            {
                'country_id': 'France',
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
        ]

        messages.append({
            "role": "system",
            "content": (
                "You are an expert at structured data extraction. "
                "Your task is to search for books that specify user criteria for each of the following countries: "
                f"{', '.join(countries)} and return them in a specified JSON structure. "
                "Make sure you do not invent any information and give the TRUE Goodreads link that actually corresponds "
                "to a book listed along with the true rating extracted from Goodreads. "
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
            goodreads_url: str
        
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

async def call_chat_concurrently(all_countries: list):
    print('----------CALLED ME ONCE-----------------')
    list_size = 30
    countries_lists = [all_countries[i: i+list_size] for i in range(0, len(all_countries), list_size)]

    # Launch concurrent calls
    results = await asyncio.gather(*[
        chat(list_chunk) for list_chunk in countries_lists
    ])
    print('-------RESULTS-------')
    # print(results)
    # response = ''.join(results)

    # bot_response_dict = response.output_parsed.model_dump()
    # bot_response_json = json.dumps(response)
    # response = ''.join(
    #      json.dumps(item.output_parsed.model_dump())
    #      for item in results
    # )

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
    response_for_user.append({'role': 'system', 'content': f'Another instance of LLM has been provided with the following system prompt and was asked to generate books based on user query specified. Give a friendly response after user asked for a request, as if it was coming from an LLM that generated the output.'})

    response_summary =  ai_client.responses.create(
        model="gpt-4o-2024-08-06",
        input = response_for_user
    )

    return jsonify({'json_response': bot_response_json, 
                    'response_summary': response_summary.output_text})



@chat_bp.route('/api/chat', methods = ['POST'])
@limiter.limit("50 per day")
def response_for_selected_countries():
     return(asyncio.run(call_chat_concurrently(all_countries)))