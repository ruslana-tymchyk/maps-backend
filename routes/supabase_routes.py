from flask import Blueprint
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from flask import request

supabase_bp = Blueprint('supabase', __name__)

# Load environment variables
load_dotenv()

# Retrieve connection details
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


@supabase_bp.route('/countries', methods = ['GET'])
def countries():

    response = (supabase.table("countries")
                .select("*")
                .execute())

    return response.data

@supabase_bp.route('/add_query', methods = ['POST'])
def add_query():
    prompt = request.json.get('prompt')  

    if not prompt:
        return "❌ Missing prompt", 400
    
    response = (supabase.table("query")
                .insert({"prompt": prompt})
                .execute())

    return response.data

@supabase_bp.route('/save_response', methods = ['POST'])
def add_response():
    chat_response = request.json.get('chat_response')  

    if not chat_response:
        return "❌ No response", 400
    
    response = (supabase.table("responses")
                .insert({"prompt": chat_response})
                .execute())

    return response.data