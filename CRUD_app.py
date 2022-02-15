# Development  project - Flask
from flask import Flask, request, render_template
from flask_restful import Api, Resource, abort, reqparse, marshal_with, fields
import random
import requests
from copy import copy
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger
import flasgger
from flask_debugtoolbar import DebugToolbarExtension


# Step1: Create a Flask app listening on port 8080
app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_ECHO'] = True
app.debug = True
app.config['SECRET_KEY'] = 'dev'

DebugToolbarExtension(app)
db = SQLAlchemy(app)
Swagger(app)

class GroceryModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(10), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    origin = db.Column(db.String(50), nullable=False) 

db.create_all()

grocery_data = {
     1: {
         "id": 1,
         "number": "GR1",
         "type": "Veg",
         "origin": "Spain",
     },
}

grocery_model_field = {
    'id': fields.Integer,
    'number': fields.String,
    'type': fields.String,
    'origin': fields.String,
}

grocery_req = reqparse.RequestParser()
grocery_req.add_argument('number', type=str, required=True)
grocery_req.add_argument('type', type=int, required=True)
grocery_req.add_argument('origin', type=str, required=True)

class GroceryList(Resource):

    #@marshal_with(grocery_model_field)
    def get(self):
        """
        returns all groceris
        ---
        responses:
            200:
                description : list of groceries
        """
        return grocery_data
        #result = GroceryModel.query.all()

        #return result


@app.route('/', methods=['GET'])
def main_page():
    return {'message': 'This is the main page'}

@app.route('/health', methods=['GET'])
def health_page():
    return {'message': 'This is the health page'}

api.add_resource(GroceryList, '/health/groceries/')

'''def webpage():
    groceries = GroceryModel.query.all()
    magic_word = 'Step4'
    return render_template('webpage.html', groceries=groceries, magic_word=magic_word)
'''
if __name__ == '__main__':
      app.run(debug = True, host='0.0.0.0', port=8080)