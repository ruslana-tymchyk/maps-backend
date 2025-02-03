from flask import Flask, request, jsonify
from firestore_service import add_allocation

# poetry run flask run --debug --port=5000

app = Flask(__name__)
app.config["DEBUG"] = True  # Enables automatic reloading

@app.route("/add_country_value", methods = ['POST'])

def add_country_value():
    data = request.json
    country_id = data.get('country_id')
    value = data.get('value')

    if not country_id or not isinstance(value, (int, float)):
        return jsonify({'error': 'Invalid input'}), 400
    
    add_allocation(country_id, value)
    return jsonify({'message': 'Allocation added successfully'}), 201

def hello_world():
    return "<p>Ori loves Lana!</p>"