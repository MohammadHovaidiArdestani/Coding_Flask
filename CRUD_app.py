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

""" grocery_data = {
     1: {
         "id": 1,
         "number": "GR1",
         "type": "Veg",
         "origin": "Spain",
     },
} """

# define the format of data so that the marshal_with can convert them later
grocery_model_field = {
    'id': fields.Integer,
    'number': fields.String,
    'type': fields.String,
    'origin': fields.String,
}

# structure of data
grocery_req = reqparse.RequestParser()
grocery_req.add_argument('number', type=str, required=True)
grocery_req.add_argument('type', type=str, required=True)
grocery_req.add_argument('origin', type=str, required=True)

grocery_req_patch = reqparse.RequestParser()
grocery_req_patch.add_argument('number', type=str, required=True)
grocery_req_patch.add_argument('type', type=str, required=True)
grocery_req_patch.add_argument('origin', type=str, required=True)
def abort_if_grocery_missing(grocery_id):
    grocery  = GroceryModel.query.get(grocery_id)

    if not grocery:
        abort(404, message='No grocery found with this id')
class Grocery(Resource):
    @marshal_with(grocery_model_field)
    def get(self, grocery_id):
        """returns a grocery
        ---
        parameters:
            - name: grocery_id
              in: path
              type: integer
              required: true
        responses:
            200:
                description: Get data related to one particular grocery
        """
        abort_if_grocery_missing(grocery_id)
        grocery = GroceryModel.query.get(grocery_id)

        return grocery

class GroceryList(Resource):

# take the new data and convert them accordingly
    @marshal_with(grocery_model_field)
    def get(self):
        """
        returns all groceris
        ---
        responses:
            200:
                description : list of groceries
        """
        #return grocery_data
        result = GroceryModel.query.all()

        return result


    @marshal_with(grocery_model_field)
    def post(self):
        new_grocery_data = grocery_req.parse_args()

        new_grocery = GroceryModel(
            number = new_grocery_data['number'],
            type = new_grocery_data['type'],
            origin = new_grocery_data['origin'],

        )

# adding the new data to our database
        db.session.add(new_grocery)
        db.session.commit()

        return new_grocery, 201


@app.route('/')
def webpage():
    groceries = GroceryModel.query.all()
    magic_word = 'Step5'
    return render_template('webpage.html', groceries=groceries, magic_word=magic_word)
#def main_page():
#    return {'message': 'This is the main page'}

@app.route('/health/', methods=['GET'])
def health_page():
    return {'message': 'This is the health page'}

@app.route('/details/<int:pk>/', methods=['GET'])
def details(pk):
    g = Grocery.get(pk)

    return render_template('details.html', g = g)


api.add_resource(GroceryList, '/groceries')


if __name__ == '__main__':
      app.run(debug = True, host='0.0.0.0', port=8080)