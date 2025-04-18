from typing import List, Optional
import json
import pandas as pd
import time

from groq import Groq
from pydantic import BaseModel
import os

from dotenv import load_dotenv

load_dotenv()

groq = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

all_countries = pd.read_csv('/Users/lana/Documents/MapsProject/maps_backend/data/countries-mledoze.csv')

# Data model for LLM to generate
class Country(BaseModel):
    country_name: str
    item_name: str
    item_description: str
    # item_metadata: Optional[dict]


# Maybe remove this structure all together and just pass it to a dict directly
class Map(BaseModel):
    # list_name: str
    # interest_name: str
    countries: List[Country]
    # directions: List[str]

def get_subregions(all_countries):
    all_countries = all_countries[all_countries['independent'] == 1]
    print('UNIQUE REGIONS')
    print(all_countries['subregion'].unique())
    return all_countries['subregion'].unique()

def get_countries_by_subregion(all_countries, subregion):
    all_countries = all_countries[all_countries['independent'] == 1]
    all_countries = all_countries[all_countries['subregion'] == subregion]
    return all_countries['name.common'].unique()

def get_map(interest_name: str, countries: list) -> Map:

    chat_completion = groq.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are an bot that searches and retrieves information on country and related items of interest. Return 1 most appropriate example for each item of interest per country in the following format. \n"
                # Pass the json schema to the model. Pretty printing improves results.
                f" The JSON object must use the schema: {json.dumps(Map.model_json_schema(), indent=2)}",
            },
            {
                "role": "user",
                "content": f"Fetch an example for the following interest {interest_name} for each of the following countries {countries} ONLY if instance of that interest exists. Do not invent any information.",
            },
        ],
        model="deepseek-r1-distill-llama-70b",

        #llama-3.3-70b-versatile  The best so far, at least does not break when I give it many countries, bit also only gives response for a few
        temperature=0, # 0 is more deterministic
        # Streaming is not supported in JSON mode
        stream=False,
        # Enable JSON mode by setting the response format
        response_format={"type": "json_object"},
    )
    return Map.model_validate_json(chat_completion.choices[0].message.content)

def get_all_maps(all_countries):
    subregions = get_subregions(all_countries)
    all_answers = {'countries': []}
    for subregion in subregions:
        countries = get_countries_by_subregion(all_countries, subregion)
        pydantic_map_answers = get_map("best movies", countries)
        dict_answers = pydantic_map_answers.model_dump()
        all_answers['countries'].extend(dict_answers['countries'])
        # time.sleep(5)
    return all_answers

# Next step: add this info to Firebase database

def print_interest(map: Map):

    for country in map.countries:
        print(
            f"- {country.country_name}: {country.item_name}. Description: {country.item_description}"
        )
# My dict_answers
# {'countries': [{'country_name': 'Angola', 'item_name': 'The Hero (O Herói)', 'item_description': 'A 2004 Angolan film directed by Zézé Gamboa, depicting the life of a former Angolan soldier.'}, 
#                {'country_name': 'Central African Republic', 'item_name': 'No notable examples', 'item_description': 'The Central African Republic does not have a prominent film industry, and no notable movies are widely recognized.'}, 
#                {'country_name': 'Cameroon', 'item_name': 'The Great White of Lambaréné', 'item_description': 'A 1995 Cameroonian film directed by Christian Goran, exploring themes of colonialism and identity.'}, 
#                {'country_name': 'DR Congo', 'item_name': 'Viva Riva!', 'item_description': 'A 2010 film directed by Djo Tunda Wa Munga, which was the first Congolese film to be submitted for Academy Award consideration.'}, 
#                {'country_name': 'Republic of the Congo', 'item_name': 'The Forest', 'item_description': 'A 2003 film by Didier Ouénangaré, addressing social issues in the Republic of the Congo.'}, 
#                {'country_name': 'Gabon', 'item_name': 'No notable examples', 'item_description': 'Gabon does not have a prominent film industry, and no notable movies are widely recognized.'}, 
#                {'country_name': 'Equatorial Guinea', 'item_name': 'No notable examples', 'item_description': 'Equatorial Guinea does not have a prominent film industry, and no notable movies are widely recognized.'}, 
#                {'country_name': 'South Sudan', 'item_name': 'The Migration', 'item_description': 'A film by Simon Bingo, highlighting the challenges faced by South Sudanese communities.'}, 
#                {'country_name': 'São Tomé and Príncipe', 'item_name': 'No notable examples', 'item_description': 'São Tomé and Príncipe does not have a prominent film industry, and no notable movies are widely recognized.'}, 
#                {'country_name': 'Chad', 'item_name': 'A Screaming Man (Un homme qui crie)', 'item_description': 'A 2010 film by Mahamat-Saleh Haroun, which won the Jury Prize at the Cannes Film Festival.'}]}

interest_maps = get_all_maps(all_countries)

# Print all interests
for interest in interest_maps:
    print_interest(interest)  # ✅ FIXED: Iterate over the list

# def print_interest(map: Map):
#     print("Interest:", map.interest_name)

#     print("\Information:")
#     for country in map.countries:
#         print(
#             f"- {country.country_name}: {country.item_name}. Description: {country.item_description}"
#         )


# interest = get_map("best movies")
# print_interest(interest)
