from flask import Flask
from flask_cors import CORS

from routes.supabase_routes import supabase_bp
from routes.chat_routes import chat_bp

from flask_app.extensions import limiter

# Create a Flask app
app = Flask(__name__)


allowed_origins = [
    'http://localhost:3000',           # Local development
    'http://127.0.0.1:3000',            # Alternative localhost
    'https://maps-frontend-two.vercel.app' # Production
]
CORS(app, origins=allowed_origins)

limiter.init_app(app)

app.register_blueprint(supabase_bp)
app.register_blueprint(chat_bp)
    
if __name__ == '__main__':
    app.run(debug=True)
    

