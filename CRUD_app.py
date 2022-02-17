# Development  project - Flask
from unittest import result
from flask import Flask, redirect, request, render_template
import flask
from flask_restful import Api, Resource, abort, reqparse, marshal_with, fields
import random
import requests
from copy import copy
from flask_accept import accept
import pyodbc
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger
import flasgger
from flask import jsonify
from flask_debugtoolbar import DebugToolbarExtension
import json
from dataclasses import dataclass
from collections import defaultdict
from sqlalchemy import inspect

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
grocery_req_patch.add_argument('number', type=str, required=False)
grocery_req_patch.add_argument('type', type=str, required=False)
grocery_req_patch.add_argument('origin', type=str, required=False)


def abort_if_grocery_missing(grocery_id):
    grocery = GroceryModel.query.get(grocery_id)

    if not grocery:
        abort(404, message='No grocery found with this id')


class GroceryList(Resource):

# take the new data and convert them accordingly
    @marshal_with(grocery_model_field)
    def get(self):
        """
        returns all groceries
        ---
        responses:
            200:
                description : list of groceries
        """
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
    
    @marshal_with(grocery_model_field)
    def put(self, grocery_id):
        abort_if_grocery_missing(grocery_id)

        data = grocery_req.parse_args()

        grocery = GroceryModel.query.get(grocery_id)
        
        grocery.number = data['number']
        grocery.origin = data['origin']
        grocery.type = data['type']

        db.session.commit()

        return grocery
    
    @marshal_with(grocery_model_field)
    def patch(self, grocery_id):
        abort_if_grocery_missing(grocery_id)
        
        data = grocery_req_patch.parse_args()

        grocery = GroceryModel.query.get(grocery_id)
        
        if data['number']:
            grocery.number = data['number']
        
        if data['origin']:
            grocery.origin = data['origin']
        
        if data['type']:
            grocery.type = data['type']
        
        db.session.commit()

        return grocery
    
    def delete(self, grocery_id):
        abort_if_grocery_missing(grocery_id)

        grocery = GroceryModel.query.get(grocery_id)

        db.session.delete(grocery)
        db.session.commit()

        return '', 204


@app.route('/', methods=["GET", "POST", "PATCH"])
def webpage():
    #handling JSON Or HTML file
    accept_header = request.headers.get('Accept', '*/*')
    if "text/html" in accept_header:
        groceries = GroceryModel.query.all()
        return render_template("webpage.html", groceries = groceries)
    else:

        results = GroceryModel.query.all()
        result = defaultdict(list)
        for obj in results:
            instance = inspect(obj)
            for key, x in instance.attrs.items():
                result[key].append(x.value)
        ids = result['id']
        numbers = result['number']
        types = result['type']
        origins = result['origin']

        lst = list()

        for i in range(len(ids)):
            a = dict()
            a["id"] = ids[i]
            a["number"] = numbers[i]
            a["type"] = types[i]
            a["origin"] = origins[i]
            lst.append(a)

        print(type(result))
        return jsonify(lst)


#handling JSON Or HTML file
def JSON_HMTL():
    #content_type = request.headers.get('Content-Type')
    if request.headers.get('ACCEPT'):
        json = request.json
        return json
    else:
        groceries = GroceryModel.query.all()
        magic_word = 'Step5'
        return render_template('webpage.html', groceries=groceries, magic_word=magic_word)

@app.route('/health/', methods=['GET'])
def health_page():
    return {'message': 'This is the health page'}

@app.route('/details/<int:id>/', methods=['GET'])
def details(id):
    g = GroceryModel.query.get(id)
    return render_template('details.html', g = g)

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        number = request.form.get('number')
        type = request.form.get('type')
        origin = request.form.get('origin')
        new_grocery = GroceryModel(
            number = number,
            type = type,
            origin = origin
        )
        db.session.add(new_grocery)
        db.session.commit()
        last_item = GroceryModel.query.order_by(GroceryModel.id.desc()).first()
        last_item_id = last_item.id
        g = GroceryModel.query.get(last_item_id)
        #Creating connection Object called conn which will contain SQL Server Connection
        conn = pyodbc.connect('Driver={ODBC Driver 17 for SQL Server};'
                              'Server=.\SQLEXPRESS;'
                              'Database=groceries;'
                              'Trusted_Connection=yes;')
        cursor = conn.cursor()
        insert_query = '''
            INSERT INTO items (id, number, type, origin) 
            VALUES (?, ?, ?, ?);'''
        values = (last_item_id, g.number, g.type, g.origin)
        cursor.execute(insert_query, values)
        conn.commit()
        conn.close()
        groceries = GroceryModel.query.all()
        magic_word = 'Step8'
        return render_template('webpage.html', groceries=groceries, magic_word=magic_word)

    return render_template('create.html')

@app.route('/delete/<int:id>/', methods=['POST'])
def delete(id):
    g = GroceryModel.query.get(id)
    db.session.delete(g)
    db.session.commit()
    groceries = GroceryModel.query.all()
    magic_word = 'Step5'
    return render_template('webpage.html', groceries=groceries, magic_word=magic_word)


@app.route('/modify/<int:id>/', methods=['GET', 'PATCH', 'POST'])
def modify(id):
    # This part is supported by postman
    if request.method == 'PATCH':
        data = grocery_req_patch.parse_args()
        grocery = GroceryModel.query.get(id)
        if data['number']:
            grocery.number = data['number']

        if data['origin']:
            grocery.origin = data['origin']

        if data['type']:
            grocery.type = data['type']

        db.session.commit()
        groceries = GroceryModel.query.all()
        magic_word = 'Step8'
        return render_template('webpage.html', groceries=groceries, magic_word=magic_word)
        # This part is supported by browser
    elif request.method == 'POST':
        data = grocery_req_patch.parse_args()
        grocery = GroceryModel.query.get(id)
        if data['number']:
            grocery.number = data['number']

        if data['origin']:
            grocery.origin = data['origin']

        if data['type']:
            grocery.type = data['type']

        db.session.commit()
        groceries = GroceryModel.query.all()
        magic_word = 'Step8'
        return render_template('webpage.html', groceries=groceries, magic_word=magic_word)

    return render_template('modify.html')

@app.route('/groceries', methods=["GET", "POST"])
def groceries_list():
    start = request.args.get('start', default=0, type=int)
    count = request.args.get('count', default=0, type=int)
    contains = request.args.get('contains')
    if contains is None:
        end_index = start+count
        index_list = list(range(start, end_index+1))
        groceries = db.session.query(GroceryModel).filter(GroceryModel.id.in_(index_list)).all()
    else:
        groceries = db.session.query(GroceryModel).filter(GroceryModel.origin.like("%" + contains + "%")).all()
    return render_template("webpage.html", groceries=groceries)


@app.route('/groceries/<int:start>/<int:count>', methods=["GET", "POST"])
def groceries_list2(start, count):
    end_index = start + count
    index_list = list(range(start, end_index+1))
    groceries = db.session.query(GroceryModel).filter(GroceryModel.id.in_(index_list)).all()
    return render_template("webpage.html", groceries = groceries)


if __name__ == '__main__':
      app.run(debug = True, host='0.0.0.0', port=8080)