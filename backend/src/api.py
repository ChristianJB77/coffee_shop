import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

"""Uncomment for re-initalizing database, watch out: Will delete entire db"""
#db_drop_and_create_all()

## ROUTES
"""GET Public drinks overview"""
@app.route('/drinks')
# Public no requires_auth
def get_drinks():
    res = Drink.query.all()
    # Abort if drinks list is empty
    if len(res) == 0:
        abort(404)
    # Format output for frontend
    drinks = [d.short() for d in res]

    return jsonify({
        "sucess": True,
        "drinks": drinks
    })


"""GET Drinks details, permission required"""
@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_details(jwt):
    res = Drink.query.all()
    # Abort if drinks list is empty
    if len(res) == 0:
        abort(404)
    # Format output for frontend
    drinks = [d.long() for d in res]

    return jsonify({
        "success": True,
        "drinks": drinks
    })


"""POST add new drinks with details"""
@app.route('/drinks', methods=["POST"])
@requires_auth('post:drinks')
def post_new_drinks(jwt):
    # Get HTML json body response
    body = request.get_json()
    # New drink with details
    new_title = body.get('title', None)
    new_recipe = body.get('recipe', None)

    #Check if title is unique
    unique_check = Drink.query.filter(Drink.title == new_title).one_or_none()
    print(unique_check)
    if unique_check != None:
        print('Title is already existing!')
        abort(409)

    #Title is unique -> Add to database
    else:
        new_drink = Drink(
            title = new_title,
            recipe = json.dumps(new_recipe)
        )
        new_drink.insert()

        # Return ONLY new drink
        res = Drink.query.filter(Drink.title == new_title)
        drink = [d.long() for d in res]
        # Check if successfully added to database
        if len(drink) == 0:
            abort(404)

        return jsonify({
            "success": True,
            "drinks": drink
        })


"""PATCH edit drinks"""
@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def edit_drinks(jwt, id):
    # Get HTML json body response
    body = request.get_json()

    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        # Check if drink to be edited is existing in database
        if drink is None:
            abort(404)

        # Edit drink
        drink.title = body.get('title', None)
        drink.recipe = json.dumps(body.get('recipe', None))
        #drink.recipe = body.get('recipe', None)
        drink.update()

        # Return ONLY edited drink
        res = Drink.query.filter(Drink.id == id)
        edited_drink = [d.long() for d in res]
        # Check if successfully added to database
        if len(edited_drink) == 0:
            abort(404)

        return jsonify({
            "success": True,
            "drinks": edited_drink
        })

    except:
        abort(400)

'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''


## Error Handling
'''
Example error handling for unprocessable entity
'''
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False,
                    "error": 422,
                    "message": "unprocessable"
                    }), 422

'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''

'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''
