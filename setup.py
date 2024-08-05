from flask import Flask, render_template, request, flash, redirect, url_for, session, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select, inspect, text, exc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.types import Integer, String, VARCHAR, Float, DateTime
from datetime import datetime
import traceback
import os

app = Flask(__name__)
#database provided by BLAKE DEJOHN
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:M1Pb6czhH8zRSfvB@stably-heuristic-elk.data-1.use1.tembo.io:5432/postgres'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = 'secret string'

db = SQLAlchemy(app)
#WRITTEN BY BLAKE DEJOHN
type_mapping = {
    Integer: 'integer',
    String: 'varchar',
    VARCHAR: 'varchar',
    Float: 'double_precision',
    DateTime: 'timestamp'
}
#WRITTEN BY BLAKE DEJOHN
#checks if tables in the database are different from the ones in the models
def check_db():
    #get the tables in the database and the models
    insepector = inspect(db.engine)
    existing_tables = insepector.get_table_names()
    model_tables = db.Model.metadata.tables.keys()
    #checking if the tables in the database are different from the ones in the models
    if set(existing_tables) != set(model_tables):
        return True
    #checking if the columns in the tables in the database are different from the ones in the models
    for table_name in model_tables:
        existing_columns = insepector.get_columns(table_name)
        model_columns = db.Model.metadata.tables[table_name].columns

        if len(existing_columns) != len(model_columns):
            return True
        
        for column in existing_columns:
            model_column = model_columns.get(column['name'])
            if model_column is None:
                print('Column', column['name'], 'does not exist in table', table_name)
                return True
            
            existing_column_type = type(column['type']).__name__.lower()
            model_column_type = type(model_column.type).__name__.lower()

            existing_column_type = type_mapping.get(type(column['type']), existing_column_type)
            model_column_type = type_mapping.get(type(model_column.type), model_column_type)

            if existing_column_type != model_column_type:
                print('Type mismatch for column', column['name'], 'in table', table_name)
                print('Existing column type:', existing_column_type)
                print('Model column type:', model_column_type)
                return True

    #if the tables and columns are the same, return False
    return False

#WRITTEN BY BLAKE DEJOHN
#checks if the database is empty
def is_db_empty():
    #get all the tables in the database
    for table in db.Model.metadata.tables.values():
        #select all from the table
        result = db.session.execute(select(table)).fetchone()
        #if result is not None, the table is not empty
        if result:
            return False
    #if all tables are empty, return True
    return True

#WRITTEN BY BLAKE DEJOHN
#use the sql script to populate the database
def populate_db():
    #get the sql script
    script = os.path.join(os.path.dirname(__file__), 'populate.sql')
    #execute the sql script
    with open(script, 'r') as f:
        sql = f.read()
    db.session.execute(text(sql))
    #commit the changes to the database
    db.session.commit()

#WRITTEN BY BLAKE DEJOHN
#initializes the database, if the tables in the database are different from the ones in the models, it drops the tables and creates new ones
#also populates the database with some data if it is empty
def init_db():
    with app.app_context():
        #if the tables in the database are different from the ones in the models, drop the tables and create new ones
        if check_db():
            print("Database schema does not match the models, dropping current tables")
            db.drop_all()
            print("Creating new tables in accordance with the models")
            db.create_all()
        #if the database is empty, populate it with data from the sql script
        if is_db_empty():
            print("Database is empty, populating with data from sql script")
            populate_db()


#WRITTEN BY JADEN WANG (art_piece entity edited by BLAKE DEJOHN)
class users(db.Model):
    user_id=db.Column(db.Integer, primary_key=True)
    user_fname=db.Column(db.String(100))
    user_lname=db.Column(db.String(100))
    email=db.Column(db.String(100), unique=True)
    password=db.Column(db.String(100))
    role=db.Column(db.String(1))

class art_piece(db.Model):
    piece_id=db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('creator.creator_id'))
    owner_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), default = 1)
    title=db.Column(db.String(100))
    year_finished=db.Column(db.Integer)
    cost=db.Column(db.Float)
    period=db.Column(db.String(200))
    photo_link=db.Column(db.String(1000))
    sellable=db.Column(db.Boolean)
    viewable=db.Column(db.Boolean)

class creator(db.Model):
    creator_id=db.Column(db.Integer, primary_key=True)
    creator_fname=db.Column(db.String(100))
    creator_lname=db.Column(db.String(100))
    birth_country=db.Column(db.String(100))
    birth_date=db.Column(db.Date)
    death_date=db.Column(db.Date)

class transaction(db.Model):
    transaction_id=db.Column(db.Integer, primary_key=True)
    piece_id = db.Column(db.Integer, db.ForeignKey('art_piece.piece_id'))
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    seller_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    timestamp=db.Column(db.DateTime, default=datetime.utcnow)

# Read creator function for display, done by Adam
def getcreator():
    return creator.query.all()

# Function to get creator names mapped to IDs, done by Adam
def get_creator_names():
    creators = creator.query.all()
    creator_names = {f"{creator.creator_fname} {creator.creator_lname}": creator.creator_id for creator in creators}
    return creator_names

# Read transaction function for display
def gettransaction():
    query = select(transaction)
    result = db.session.execute(query)

    transaction_list = []
    for transactions in result.scalars():
        chosen_art_piece=db.session.query(art_piece).filter(art_piece.piece_id== transactions.piece_id).first()
        buyer=db.session.query(users).filter(users.user_id== transactions.buyer_id).first()
        seller=db.session.query(users).filter(users.user_id== transactions.seller_id).first()
        transaction_list.append((chosen_art_piece.title, buyer.user_fname, buyer.user_lname, seller.user_fname, seller.user_lname, transactions.timestamp))
    return transaction_list

# Function to get user names mapped to IDs
def get_art_piece_titles():
    query = select(art_piece)
    result = db.session.execute(query)
    
    art_piece_titles = {}
    for chosen_art_piece in result.scalars():
        full_title = f"{chosen_art_piece.title}"
        art_piece_titles[full_title] = chosen_art_piece.piece_id
    return art_piece_titles

# Function to get user names mapped to IDs
def get_user_names():
    query = select(users)
    result = db.session.execute(query)
    
    user_names = {}
    for user in result.scalars():
        full_name = f"{user.user_fname} {user.user_lname}"
        user_names[full_name] = user.user_id
    return user_names

# Function to get transaction info mapped to IDs
def get_transaction_info():
    query = select(transaction)
    result = db.session.execute(query)
    
    transaction_info = {}
    for transactions in result.scalars():
        chosen_art_piece=db.session.query(art_piece).filter(art_piece.piece_id== transactions.piece_id).first()
        buyer=db.session.query(users).filter(users.user_id== transactions.buyer_id).first()
        seller=db.session.query(users).filter(users.user_id== transactions.seller_id).first()
        if(session['admin']):
            full_info = f"{chosen_art_piece.title} {buyer.user_fname} {buyer.user_lname} {seller.user_fname} {seller.user_lname} {transactions.timestamp}"
            transaction_info[full_info] = transactions.transaction_id
        elif((buyer.user_id==session['user_id'] or seller.user_id==session['user_id'])):
            full_info = f"{chosen_art_piece.title} {buyer.user_fname} {buyer.user_lname} {seller.user_fname} {seller.user_lname} {transactions.timestamp}"
            transaction_info[full_info] = transactions.transaction_id
    return transaction_info
