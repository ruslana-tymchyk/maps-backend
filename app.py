from flask import Flask
from flask_cors import CORS
import os

import logging
logging.basicConfig(level=logging.INFO)

from routes.supabase_routes import supabase_bp
from routes.chat_routes import chat_bp

from flask_app.extensions import limiter

print(f"PORT environment variable: {os.environ.get('PORT', 'NOT SET')}")
# Create a Flask app
app = Flask(__name__)

# allowed_origins = [
#     'http://localhost:3000',           # Local development
#     'http://127.0.0.1:3000',            # Alternative localhost
#     'https://maps-frontend-two.vercel.app' # Production
# ]
# CORS(app, origins=allowed_origins)
CORS(app)

limiter.init_app(app)

app.register_blueprint(supabase_bp)
app.register_blueprint(chat_bp)
    
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Flask app on port {port}")
    try:
        app.run(host="0.0.0.0", port=port, debug=True)
    except Exception as e:
        print(f"Error starting app: {e}")
    

