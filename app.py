from flask import Flask, render_template, request, flash, redirect, url_for, session, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select, inspect, text, exc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.types import Integer, String, VARCHAR, Float, DateTime
from datetime import datetime
import os
import traceback
import psycopg2

type_mapping = {
    Integer: 'integer',
    String: 'varchar',
    VARCHAR: 'varchar',
    Float: 'double_precision',
    DateTime: 'timestamp'
}

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

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:M1Pb6czhH8zRSfvB@stably-heuristic-elk.data-1.use1.tembo.io:5432/postgres'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = 'secret string'

db = SQLAlchemy(app)

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

class users(db.Model):
    user_id=db.Column(db.Integer, primary_key=True)
    user_fname=db.Column(db.String(100))
    user_lname=db.Column(db.String(100))
    email=db.Column(db.String(100), unique=True)
    password=db.Column(db.String(100))
    role=db.Column(db.String(1))

class transaction(db.Model):
    transaction_id=db.Column(db.Integer, primary_key=True)
    piece_id = db.Column(db.Integer, db.ForeignKey('art_piece.piece_id'))
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    seller_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    timestamp=db.Column(db.DateTime, default=datetime.utcnow)

init_db()

@app.route("/", methods=['GET','POST'])
def index():
    session['admin'] = False
    if request.method == 'POST':
        #get the email and password from the form
        email = request.form['email']
        password = request.form['password']

        #find the user with the inputted email in the database
        user = users.query.filter_by(email=email).first()
        #if the user exists and the password is correct, log them in
        if user and user.password == password:
            # flash('You have been logged in', 'success')
            session["user_email"] = email
            session["user_password"] = password
            session["user_id"] = users.query.filter(users.email == email).first().user_id
            session["admin"] = users.query.filter(users.email == email).first().role == 'A'
            return redirect(url_for('home'))
        else:
            #if the user does not exist or the password is incorrect, flash an error message
            flash('Invalid email or password', 'danger')
            return render_template("index.html")
    return render_template("index.html")

# function to direct user to home after login
@app.route('/home')
def home():
    if session['admin']:
        return render_template('home.html')
    else:
        return redirect(url_for('home_patron'))
    
@app.route('/home_patron')
def home_patron():
    return render_template('home_patron.html')

@app.route('/paintings', methods = ['GET'])
def paintings():
    #used for page stuff
    page = request.args.get('page', 1, type=int)
    query = request.args.get('query', '', type=str)
    sort_by = request.args.get('sort_by', 'title', type=str)
    #can change this to whatever, decides how many paintings are shown per page
    per_page = 5

    # does the user want to search for a painting?
    if query:
        #filter based on what they searched for
        paintings_query = art_piece.query.filter(art_piece.title.ilike(f'%{query}%'))
    else:
        #else just get all the paintings that are viewable
        paintings_query = art_piece.query.filter(art_piece.viewable == True)
    
    #find out how the user wants to sort the paintings and sort accordingly
    if sort_by == 'title':
        paintings_query = paintings_query.order_by(art_piece.title)
    elif sort_by == 'year':
        paintings_query = paintings_query.order_by(art_piece.year_finished)
    
    #paginate the paintings (basically separates them into pages)
    paintings = paintings_query.paginate(page=page, per_page=per_page)
    #get all the creators so we can display the artist of each painting
    all_creators = creator.query.all()

    #get all the users so we can display the owner of each painting
    owners = users.query.all()

    #render the paintings page with all the required info
    return render_template("paintings.html", paintings = paintings.items, creators = all_creators, owners=owners , pagination = paintings, query=query, sort_by = sort_by)

@app.route('/buy_menu', methods = ['GET'])
def buy_menu():
    #used for page stuff
    page = request.args.get('page', 1, type=int)
    query = request.args.get('query', '', type=str)
    sort_by = request.args.get('sort_by', 'title', type=str)
    #can change this to whatever, decides how many paintings are shown per page
    per_page = 5

    # does the user want to search for a painting?
    if query:
        #filter based on what they searched for
        paintings_query = art_piece.query.filter(art_piece.title.ilike(f'%{query}%'), art_piece.sellable == True)
    else:
        #else just get all the paintings that are sellable
        paintings_query = art_piece.query.filter(art_piece.sellable == True)
    
    #find out how the user wants to sort the paintings and sort accordingly
    if sort_by == 'title':
        paintings_query = paintings_query.order_by(art_piece.title)
    elif sort_by == 'year':
        paintings_query = paintings_query.order_by(art_piece.year_finished)
    
    #paginate the paintings (basically separates them into pages)
    paintings = paintings_query.paginate(page=page, per_page=per_page)
    #get all the creators so we can display the artist of each painting
    all_creators = creator.query.all()
    #render the paintings page with all the required info
    return render_template("buy_menu.html", paintings = paintings.items, creators = all_creators, pagination = paintings, query=query, sort_by = sort_by)

@app.route('/buy_painting/<int:piece_id>', methods = ['POST'])
def buy_painting(piece_id):
    # TODO: ask the user once they buy a painting if they want to keep it in the gallery. If not then viewable will be set to false and the painting will then have the requirements to be deleted from the database (sellable & viewable = false means the painting should be deleted)
    #might tweak this later
    buyer_email = session.get("user_email")
    if not buyer_email:
        flash('You must be logged in to buy a painting', 'danger')
        return redirect(url_for('index'))
    
    buyer = users.query.filter_by(email=buyer_email).first()
    if not buyer:
        flash('User not found', 'danger')
        return redirect(url_for('index'))
    
    painting = art_piece.query.get(piece_id)
    if painting and painting.sellable:
        #painting is no longer sellable after being bought
        painting.sellable = False

        #create a transaction for the purchase
        trans = transaction(piece_id=piece_id, buyer_id=buyer.user_id, seller_id=painting.owner_id)

        #change the owner of the painting to the buyer
        painting.owner_id = buyer.user_id
        db.session.add(trans)
        db.session.commit()
        flash(f'Painting "{painting.title}" purchased successfully', 'success')
        return redirect(url_for('buy_menu'))
    else:
        flash('Painting not found or not sellable', 'danger')
        return "Painting not available for purchase", 404

@app.route('/delete_paintings', methods = ['GET', 'POST'])
def delete_paintings():
    user_email = session.get("user_email")
    if not user_email:
        flash('You must be logged in to delete a painting', 'danger')
        return redirect(url_for('index'))
    
    user = users.query.filter_by(email=user_email).first()
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('index'))
    user_role = user.role

    if request.method == 'POST':
        #get the id of the painting to delete
        painting_id = request.form['painting_id']
        try:
            #try and delete the painting
            painting = art_piece.query.get(painting_id)
            if painting:
                db.session.delete(painting)
                db.session.commit()
                flash(f'Painting "{painting.title}" deleted successfully', 'success')
            else:
                flash('Painting not found', 'danger')
        except IntegrityError as e:
            #if the painting is referenced in another table, it can't be deleted (foreign key constraint)
            db.session.rollback()
            flash(f'Error deleting painting: This painting is referenced in another table and therefore can not be deleted as to keep foreign key integrity.', 'danger')
        except Exception as e:
            #handle any other unexpected errors
            db.session.rollback()
            flash(f'Error deleting painting: {e}', 'danger')
        #go back to the delete paintings page
        return redirect(url_for('delete_paintings'))
    #based on the user role, either show all paintings or only the ones they own
    if user_role == 'A':
        paintings = art_piece.query.all()
    else:
        paintings = art_piece.query.filter_by(owner_id=user.user_id).all()
    #render the delete paintings page with all the paintings
    return render_template("d_painting.html", paintings = paintings)

@app.route('/create_painting', methods = ['GET', 'POST'])
def create_painting():
    if request.method == 'POST':
        title = request.form.get('title')
        #default owner of the painting is the museum
        owner = 1
        creator_id = request.form.get('creator_id')
        period = request.form.get('period')
        year_finished = request.form.get('year_finished')
        cost = request.form.get('cost')
        photo_link = request.form.get('photo_link')
        sellable = request.form.get('sellable') == 'true'
        viewable = request.form.get('viewable') == 'true'

        if not title or not period or not cost or not photo_link or not year_finished:
            flash('Please fill out all fields', 'danger')
            return redirect(url_for('create_painting'))
    
        new_painting = art_piece(owner_id=owner, creator_id=creator_id, title=title, year_finished=year_finished, period=period, cost=cost, photo_link=photo_link, sellable=sellable, viewable=viewable)

        try:
            db.session.add(new_painting)
            db.session.commit()
            flash(f'Painting "{title}" created successfully', 'success')
            return redirect(url_for('create_painting'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating painting: {e}', 'danger')
            return redirect(url_for('create_painting'))
    creators = creator.query.all()
    return render_template("c_painting.html", creators=creators)



@app.route('/update_paintings', methods=['GET', 'POST'])
def update_paintings():
    if request.method == 'POST':
        try:
            piece_id = request.form['piece_id']
            painting = art_piece.query.get(piece_id)
            painting.title = request.form['title']
            painting.creator_id = request.form['creator_id']
            painting.period = request.form['period']
            painting.year_finished = request.form['year_finished']
            painting.cost = request.form['cost']
            painting.photo_link = request.form['photo_link']
            painting.sellable = 'sellable' in request.form
            painting.viewable = 'viewable' in request.form
            db.session.commit()
            flash(f'Painting "{painting.title}" updated successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating painting: {e}', 'danger')
    
    paintings = art_piece.query.order_by(art_piece.piece_id).all()
    creators = creator.query.all()
    return render_template("u_painting.html", paintings=paintings, creators=creators)


#this is the main function that runs the app
if __name__ == '__main__':
    app.run(debug = True)

# Read creator function for display
def getcreator():
    return creator.query.all()

# Function to get creator names mapped to IDs
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

@app.route("/readcreator")
def readcreators():
    try:
        creator_list = getcreator()
        return render_template("r_creator.html", creatorlist=creator_list)
    except Exception as e:
        print("Error in readcreators function:")
        print(e)
        traceback.print_exc()
        return "An error occurred while fetching the creators.", 500

@app.route("/readtransaction")
def readtransactions():
    # Get all the transactions using the getcreator function
    query = select(transaction)
    result = db.session.execute(query)

    transaction_list = []
    for transactions in result.scalars():
        chosen_art_piece=db.session.query(art_piece).filter(art_piece.piece_id== transactions.piece_id).first()
        buyer=db.session.query(users).filter(users.user_id== transactions.buyer_id).first()
        seller=db.session.query(users).filter(users.user_id== transactions.seller_id).first()
        if(session['admin']):
            transaction_list.append((chosen_art_piece.title, buyer.user_fname, buyer.user_lname, seller.user_fname, seller.user_lname, transactions.timestamp))
        elif((buyer.user_id==session['user_id'] or seller.user_id==session['user_id'])):
            transaction_list.append((chosen_art_piece.title, buyer.user_fname, buyer.user_lname, seller.user_fname, seller.user_lname, transactions.timestamp))

    # Render the read transactions page with all the required info
    return render_template("r_transaction.html", transactionlist=transaction_list)

# update creator function to allow modification 
@app.route("/updatecreator")
def updatecreators(feedback_message=None, feedback_type=False):
    creator_names = get_creator_names()
    return render_template("u_creator.html", 
                           creatornames=creator_names.keys(), 
                           feedback_message=feedback_message, 
                           feedback_type=feedback_type)

# update transaction function to allow modification 
@app.route("/updatetransaction")
def updatetransactions(feedback_message=None, feedback_type=False):
    transaction_infos = get_transaction_info()
    art_pieces=get_art_piece_titles()
    users=get_user_names()
    return render_template("u_transaction.html", 
                           transactioninfos=transaction_infos.keys(),
                           artpieces=art_pieces.keys(),
                           buyers=users.keys(),
                           sellers=users.keys(), 
                           feedback_message=feedback_message, 
                           feedback_type=feedback_type)

@app.route("/creatorupdate", methods=['POST'])
def creatorupdate():
    creator_name = request.form.get('creatornames')
    creator_fname = request.form["cfname"]
    creator_lname = request.form["clname"]
    birth_country = request.form["country"]
    birth_date = request.form["bdate"]
    death_date = request.form["ddate"]

    creator_names = get_creator_names()
    creator_id = creator_names.get(creator_name)
    
    if not creator_id:
        return updatecreators(feedback_message=f'Creator {creator_name} not found.', feedback_type=False)
    
    try:
        obj = creator.query.filter_by(creator_id=creator_id).first()
        
        if not obj:
            return updatecreators(feedback_message=f'Creator {creator_name} not found.', feedback_type=False)

        if creator_fname:
            obj.creator_fname = creator_fname
        if creator_lname:
            obj.creator_lname = creator_lname
        if birth_country:
            obj.birth_country = birth_country
        if birth_date:
            obj.birth_date = birth_date
        if death_date:
            obj.death_date = death_date

        db.session.commit()
        return updatecreators(feedback_message=f'Successfully updated creator {creator_name}', feedback_type=True)
    except Exception as err:
        db.session.rollback()
        return updatecreators(feedback_message=str(err), feedback_type=False)

@app.route("/transactionupdate", methods=['POST'])
def transactionupdate():
    if(session['admin']):
        # change transaction piece id to new art piece, transaction buyer_id to new buyer (and change art_piece owner to new buyer), transaction seller_id to new seller, timestamp to new timestamp
        transaction_info = request.form.get('transactioninfos')
        title = request.form.get('artpieces')
        buyer = request.form.get('buyers')
        seller= request.form.get('sellers')
        timestamp = request.form["timestamp"]

        transaction_infos = get_transaction_info()
        if transaction_info in transaction_infos:
            transaction_id = transaction_infos[transaction_info]
        
        try:
            obj = db.session.query(transaction).filter(
                transaction.transaction_id == transaction_id).first()
            
            if obj is None:
                msg = 'Transaction {} not found.'.format(transaction_info)
                return updatetransactions(feedback_message=msg, feedback_type=False)

            art_piece_titles = get_art_piece_titles()
            
            if title in art_piece_titles:
                art_piece_id = art_piece_titles[title]
            try:
                old_art_piece_obj=db.session.query(art_piece).filter(
                art_piece.piece_id == obj.piece_id).first()
                new_art_piece_obj=db.session.query(art_piece).filter(
                art_piece.piece_id == art_piece_id).first()
                
                if new_art_piece_obj is None:
                    msg = 'Art Piece {} not found.'.format(title)
                    return updatetransactions(feedback_message=msg, feedback_type=False)
                else:
                    old_art_piece_obj.owner_id=obj.seller_id
                    obj.piece_id = art_piece_id
                    new_art_piece_obj.owner_id=obj.buyer_id
            
            except Exception as err:
                db.session.rollback()
                return updatetransactions(feedback_message=str(err), feedback_type=False)

            user_names = get_user_names()
            
            if buyer in user_names:
                buyer_id = user_names[buyer]
            try:
                buyer_obj=db.session.query(users).filter(
                users.user_id == buyer_id).first()
                if buyer_obj is None:
                    msg = 'Buyer {} not found.'.format(buyer)
                    return updatetransactions(feedback_message=msg, feedback_type=False)
                else:
                    chosen_art_piece=db.session.query(art_piece).filter(art_piece.piece_id == obj.piece_id).first()
                    chosen_art_piece.owner_id=buyer_id
                    obj.buyer_id = buyer_id
            
            except Exception as err:
                db.session.rollback()
                return updatetransactions(feedback_message=str(err), feedback_type=False)

            if seller in user_names:
                seller_id = user_names[seller]
            try:
                seller_obj=db.session.query(users).filter(
                users.user_id == seller_id).first()
                if seller_obj is None:
                    msg = 'Seller {} not found.'.format(seller)
                    return updatetransactions(feedback_message=msg, feedback_type=False)
                else:
                    obj.seller_id = seller_id
            
            except Exception as err:
                db.session.rollback()
                return updatetransactions(feedback_message=str(err), feedback_type=False)
            
            if timestamp != '':
                obj.timestamp = timestamp

            db.session.commit()
            return updatetransactions(feedback_message='Successfully updated transaction {}'.format(transaction_info),feedback_type=True)
        except Exception as err:
            db.session.rollback()
            return updatetransactions(feedback_message=str(err), feedback_type=False)
    else:
        return updatetransactions(feedback_message='You do not have permission to update transactions',feedback_type=False)

# create creator function 
@app.route("/createcreator")
def createcreator(feedback_message=None, feedback_type=False):
    return render_template("c_creator.html",
            feedback_message=feedback_message, 
            feedback_type=feedback_type)

@app.route("/creatorcreate", methods=['POST'])
def creatorcreate():
    creator_fname = request.form["cfname"]
    creator_lname = request.form["clname"]
    birth_country = request.form["country"]
    birth_date = request.form["bdate"]
    death_date = request.form["ddate"]
    nobdate = request.form.get("nobdate")
    ifalive = request.form.get("ifalive")

    if nobdate == 'on':
        birth_date = None
    elif birth_date == '':
        return createcreator(feedback_message='Birth date is required unless "Unknown Birth Date" is checked.', feedback_type=False)

    if ifalive == 'on':
        death_date = None
    elif death_date == '':
        return createcreator(feedback_message='Death date is required unless "Unknown or Alive" is checked.', feedback_type=False)

    # Check if a creator with the same first name and last name already exists
    existing_creator = db.session.query(creator).filter_by(
        creator_fname=creator_fname, creator_lname=creator_lname).first()

    if existing_creator:
        return createcreator(feedback_message=f'A creator named {creator_fname} {creator_lname} already exists.', feedback_type=False)

    # Check if birth date and death date are missing
    if birth_date is None and nobdate != 'on':
        return createcreator(feedback_message='Birth date is required unless "Unknown Birth Date" is checked.', feedback_type=False)
    
    if death_date is None and ifalive != 'on':
        return createcreator(feedback_message='Death date is required unless "Unknown or Alive" is checked.', feedback_type=False)

    try:
        new_creator = creator(
            creator_fname=creator_fname, 
            creator_lname=creator_lname, 
            birth_country=birth_country, 
            birth_date=birth_date, 
            death_date=death_date
        )
        db.session.add(new_creator)
        db.session.commit()
        return createcreator(feedback_message=f'Successfully added creator {creator_fname} {creator_lname}', feedback_type=True)
    except Exception as err:
        db.session.rollback()
        return createcreator(feedback_message=f'Database error: {err}', feedback_type=False)

# create transaction function 
@app.route("/createtransaction")
def createtransaction(feedback_message=None, feedback_type=False):
    transaction_infos = get_transaction_info()
    art_pieces=get_art_piece_titles()
    users=get_user_names()
    return render_template("c_transaction.html", 
                           transactioninfos=transaction_infos.keys(),
                           artpieces=art_pieces.keys(),
                           buyers=users.keys(),
                           sellers=users.keys(), 
                           feedback_message=feedback_message, 
                           feedback_type=feedback_type)



@app.route("/transactioncreate", methods=['POST'])
def transactioncreate():
    if(session['admin']):
        title = request.form.get('artpieces')
        buyer = request.form.get('buyers')
        seller= request.form.get('sellers')
        timestamp = request.form["timestamp"]

        try:
            chosen_art_piece=db.session.query(art_piece).filter(art_piece.title == title).first()
            user_names = get_user_names()
            
            if buyer in user_names:
                buyer_id = user_names[buyer]
            else:
                return createtransaction(feedback_message='Buyer not found.', feedback_type=False)
            
            try:
                buyer_obj = db.session.query(users).filter(
                    users.user_id == buyer_id).first()
            
                if buyer_obj is None:
                    msg = f'Buyer {buyer} not found.'
                    return createtransaction(feedback_message=msg, feedback_type=False)
            except Exception as err:
                db.session.rollback()
                return createtransaction(feedback_message=str(err), feedback_type=False)
            
            if seller in user_names:
                seller_id = user_names[seller]
            else:
                return createtransaction(feedback_message='Buyer not found.', feedback_type=False)
            
            try:
                seller_obj = db.session.query(users).filter(
                    users.user_id == seller_id).first()
            
                if seller_obj is None:
                    msg = f'Seller {seller} not found.'
                    return createtransaction(feedback_message=msg, feedback_type=False)
            except Exception as err:
                db.session.rollback()
                return createtransaction(feedback_message=str(err), feedback_type=False)
            
            if(seller_obj.user_id==chosen_art_piece.owner_id):
                entry = transaction(piece_id=chosen_art_piece.piece_id, buyer_id=buyer_obj.user_id, seller_id=seller_obj.user_id, timestamp=timestamp)
                db.session.add(entry)
                chosen_art_piece.owner_id=buyer_obj.user_id
                db.session.commit()
            else:
                return createtransaction(feedback_message='Incorrect seller {}'.format(title),
                        feedback_type=False)
        except exc.IntegrityError as err:
            db.session.rollback()
            return createtransaction(feedback_message='A transaction with this info already exists. Create a transaction with different info.'.format(title), feedback_type=False)
        except Exception as err:
            db.session.rollback()
            return createtransaction(feedback_message='Database error: {}'.format(err), feedback_type=False)

        return createtransaction(feedback_message='Successfully added transaction {}'.format(title), feedback_type=True)
    return createtransaction(feedback_message='You do not have permission to add a transaction', feedback_type=False)

# create delete creator function 
@app.route("/deletecreator")
def deletecreator(feedback_message=None, feedback_type=False):
    creator_names = get_creator_names()
    return render_template("d_creator.html", 
                           creatornames=creator_names.keys(), 
                           feedback_message=feedback_message, 
                           feedback_type=feedback_type)

# create delete transaction function 
@app.route("/deletetransaction")
def deletetransaction(feedback_message=None, feedback_type=False):
    transaction_infos = get_transaction_info()
    return render_template("d_transaction.html", 
                           transactioninfos=transaction_infos.keys(), 
                           feedback_message=feedback_message, 
                           feedback_type=feedback_type)

@app.route("/creatordelete", methods=['POST'])
def creatordelete():
    creator_name = request.form.get('creatornames')

    # if not request.form.get('confirmInput'):
    #     return deletecreator(feedback_message='Operation canceled. Creator not deleted.', feedback_type=False)
    
    creator_names = get_creator_names()
    creator_id = creator_names.get(creator_name)

    if not creator_id:
        return deletecreator(feedback_message=f'Creator {creator_name} not found.', feedback_type=False)

    try:
        obj = creator.query.filter_by(creator_id=creator_id).first()
        
        if not obj:
            return deletecreator(feedback_message=f'Creator {creator_name} not found.', feedback_type=False)
        
        # Check if the creator is associated with any art pieces
        associated_art_pieces = db.session.query(art_piece).filter_by(creator_id=creator_id).all()
        if associated_art_pieces:
            return deletecreator(feedback_message=f'Creator {creator_name} is associated with an art piece, and cannot be deleted.', feedback_type=False)

        db.session.delete(obj)
        db.session.commit()
        return deletecreator(feedback_message=f'Successfully deleted creator {creator_name}', feedback_type=True)
    except Exception as err:
        db.session.rollback()
        return deletecreator(feedback_message=f'Database error: {err}', feedback_type=False)

@app.route("/transactiondelete", methods=['POST'])
def transactiondelete():
    if(session['admin']):
        # give ownership of art piece back to seller
        transaction_info = request.form.get('transactioninfos')
        
        transaction_infos = get_transaction_info()
        if transaction_info in transaction_infos:
            transaction_id = transaction_infos[transaction_info]
        else:
            return deletetransaction(feedback_message='Transaction not found.', feedback_type=False)

        try:
            obj = db.session.query(transaction).filter(
                transaction.transaction_id == transaction_id).first()
            
            if obj is None:
                msg = f'Transaction not found.'
                return deletetransaction(feedback_message=msg, feedback_type=False)
            chosen_art_piece=db.session.query(art_piece).filter(art_piece.piece_id== obj.piece_id).first()
            chosen_art_piece.owner_id=obj.seller_id
            db.session.delete(obj)
            db.session.commit()
        except Exception as err:
            db.session.rollback()
            return deletetransaction(feedback_message=str(err), feedback_type=False)

        return deletetransaction(feedback_message=f'Successfully deleted transaction', feedback_type=True)
    return deletetransaction(feedback_message=f'You do not have permissio to delete transaction', feedback_type=False)

@app.route("/usercreate", methods=['get'])
def usercreate():
    msg = session.get('msg', None)
    successs = session.get('feedback_type', False)
    try:
        session['feedback_type'] = False
        session.pop('msg')
    except:
        msg = None
    return render_template('c_user.html', admin=session['admin'], feedback_message=msg, feedback_type=successs)

@app.route("/usercreate_temp")
def usercreate_temp():
    fname = request.args.get('ufname')
    lname = request.args.get('ulname')
    email = request.args.get('email')
    pwd = request.args.get('password')
    role = request.args.get('role')

    if fname and lname and pwd and role and email:
        existing_user = users.query.filter_by(email=email).first()
        if existing_user:
            session['msg'] = 'Create failed: Email already exists.'
        else:
            new_user = users(
                user_fname=fname,
                user_lname=lname,
                email=email,
                password=pwd,
                role=role
            )
            try:
                db.session.add(new_user)
                db.session.commit()
                session['msg'] = 'user create success'
                session['feedback_type'] = True
            except:
                session['msg'] = 'Create Failed'
    else:
        session['msg'] = 'Create failed: missing input'
    return redirect('/usercreate')

@app.route("/userread")
def userread():
    userlist = []
    if session['admin']:
        result = db.session.execute(select(users))
    else:
        result = db.session.execute(select(users).where(users.user_id == session['user_id']))

    for user in result.scalars():
        userlist.append((user.user_fname, user.user_lname, user.email, user.password, user.role))    

    return render_template('r_user.html', userlist=userlist, admin=session['admin'])

@app.route("/userupdate", methods=['get'])
def userupdate():
    userlist = []
    if session['admin']:
        result = db.session.execute(select(users))
    else:
        result = db.session.execute(select(users).where(users.user_id == session['user_id']))

    for user in result.scalars():
        userlist.append((user.user_fname, user.user_lname, user.email, user.password, user.role))  

    msg = session.get('msg', None)
    successs = session.get('feedback_type', False)
    try:
        session['feedback_type'] = False
        session.pop('msg')
    except:
        msg = None
    
    return render_template('u_user.html', userlist=userlist, admin=session['admin'], feedback_message=msg, feedback_type=successs)

@app.route("/userupdate_temp", methods=['get'])
def userupdate_temp():
    account=request.args.get('usernames')
    fname=request.args.get('ufname')
    lname=request.args.get('ulname')
    email=request.args.get('email')
    pwd=request.args.get('password')
    role=request.args.get('role')

    print(account, fname, lname, email, pwd, role)
    if account and (fname or lname or email or pwd or role):
        try:
            user_to_update = users.query.filter_by(email=account).first()
            if user_to_update:
                session['msg'] = 'User update success'
                session['feedback_type'] = True
                # Update user attributes if new values are provided
                if email:
                    existing_user = users.query.filter_by(email=email).first()
                    if existing_user:
                        session['msg'] = 'Update failed: Email already exists.'
                        session['feedback_type'] = False
                        return redirect('userupdate')
                    else:
                        user_to_update.email = email
                if fname:
                    user_to_update.user_fname = fname
                if lname:
                    user_to_update.user_lname = lname
                if pwd:
                    user_to_update.password = pwd
                if role:
                    user_to_update.role = role

                # Commit the changes to the database
                db.session.commit()
            else:
                session['msg'] = 'User update failed: No user with this username found.'
        except Exception as e:
            session['msg'] = f'User update failed: An error occurred. {str(e)}'
    else:
        session['msg'] = 'User update failed: Missing required fields or account identifier.'

    return redirect("/userupdate")

@app.route("/userdelete", methods=['get'])
def userdelete():
    userlist = []
    if session['admin']:
        result = db.session.execute(select(users))
    else:
        result = db.session.execute(select(users).where(users.user_id == session['user_id']))

    for user in result.scalars():
        userlist.append(user.email) 

    msg = session.get('msg', None)
    successs = session.get('feedback_type', False)
    try:
        session['feedback_type'] = False
        session.pop('msg')
    except:
        msg = None

    return render_template('d_user.html', userlist=userlist, msg=msg, admin=session['admin'], feedback_message=msg, feedback_type=successs)

@app.route("/userdelete_temp", methods=['get'])
def userdelete_temp():
    get_flashed_messages()
    email=request.args.get('useremail')

    if email or not email:
        try:
            user_to_delete = users.query.filter_by(email=email).first()
            db.session.delete(user_to_delete)
            db.session.commit()
            session['msg'] = 'User delete success'
            session['feedback_type'] = True

        except IntegrityError as e:
            session['msg'] = 'User delete fail. Integrity Error'
            session['feedback_type'] = False
    return redirect("/userdelete")