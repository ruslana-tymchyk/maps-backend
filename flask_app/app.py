from flask import Flask
from flask_cors import CORS

from routes.supabase_routes import supabase_bp
from routes.chat_routes import chat_bp

from extensions import limiter

# Create a Flask app
app = Flask(__name__)
CORS(app) #to call api from local server

limiter.init_app(app)

app.register_blueprint(supabase_bp)
app.register_blueprint(chat_bp)
    
if __name__ == '__main__':
    app.run(debug=True)
    

