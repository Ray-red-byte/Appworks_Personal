from flask import Flask, render_template
from flask import request, jsonify, make_response
import os
from werkzeug.security import generate_password_hash, check_password_hash
from function import check_exist_row, validate_email, create_token, authentication
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# JWT secret key
jwt_secret_key = os.getenv('JWT_SECRET_KEY')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/user/login_token', methods=['POST'])
def login_token():
    if request.method == 'POST':
        content_type = request.headers.get('Content-Type')

        if content_type != 'application/json':
            return jsonify({'error': 'wrong Content-type'}, 400)

        form_data = request.get_json()
        user_name = form_data["username"]
        '''
        # Check if email exists
        user_id = check_exist_row("user", "email", form_data["email"])

        if not user_id:
            response_data = {"Error": 'Invalid email'}
            return response_data

        # Retrieve user data from MongoDB
        user_data = collection.find_one({"id": user_id})

        # Check if password is correct
        if not check_password_hash(user_data["password"], form_data["password"]):
            response_data = {"Error": 'Invalid password'}
            return response_data
        '''
        
        token = create_token(user_name, jwt_secret_key)
        print(token)


        # Create a response object
        response = make_response()

        # Set the token in the response header
        response.headers["Authorization"] = f"Bearer {token}"
        return response

    else:
        response_data = {"Error": "Invalid Content-Type"}
        return response_data
    

@app.route('/register')
def register():
    return render_template('register.html')


@app.route("/user/register_token", methods=['GET', 'POST'])
def register_token():
    if request.method == 'POST':
        content_type = request.headers.get('Content-Type')

        if content_type != 'application/json':
            return jsonify({'error': 'wrong Content-type'}, 400)

        form_data = request.get_json()

        # Check if email exists
        

        if user_id:
            response_data = {"Error": 'Exist email'}
            return response_data

        # Check email validation
        if not validate_email(form_data["email"]):
            response_data = {"Error": "Invalid email"}
            return response_data

        # Insert into USER table
        password_hash = generate_password_hash(form_data["password"])


        del user_data[0]["password"]
        token = create_token(str(user_id), jwt_secret_key)
        response_data = {}
        response_data["data"] = {}
        response_data["data"]["access_token"] = token
        response_data["data"]["access_expired"] = 3600
        response_data["data"]["user"] = user_data

        # Create a response object
        response = make_response(response_data)

        # Set the token in the response header
        response.headers["Authorization"] = f"Bearer {token}"
        return response

    else:
        response_data = {"Error": "Invalid Content-Type"}
        return response_data
    

# Flask routes
@app.route('/main')
def main_page():

    # Retrieve the parameters from the query st ring
    token = request.headers.get("Authorization")

    # Call the authentication function to verify the token
    user_id = authentication(token, jwt_secret_key)

    return render_template('main.html', username=user_id)

    



@app.route('/search')
def search():
    # Implement your house search functionality here
    return "Search results will be displayed here"





if __name__ == '__main__':

    # Start WebSocket server in a separate thread
    # Start Flask server
    app.run(port=5000)

    #start_websocket_server()

    