from flask import Flask, render_template, request, flash, redirect, url_for, session, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select, inspect, text, exc
from sqlalchemy.types import Integer, String, VARCHAR, Float, DateTime
from datetime import datetime
import os
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

class Users(db.Model):
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
    if request.method == 'POST':
        #get the email and password from the form
        email = request.form['email']
        password = request.form['password']

        #find the user with the inputted email in the database
        user = Users.query.filter_by(email=email).first()
        #if the user exists and the password is correct, log them in
        if user and user.password == password:
            flash('You have been logged in', 'success')
            session["user_email"] = email
            session["user_password"] = password
            session["user_id"] = Users.query.filter(Users.email == email).first().user_id
            session["admin"] = Users.query.filter(Users.email == email).first().role == 'A'
            return redirect(url_for('paintings'))
        else:
            #if the user does not exist or the password is incorrect, flash an error message
            flash('Invalid email or password', 'danger')
            return render_template("index.html")
    return render_template("index.html")

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
    #render the paintings page with all the required info
    return render_template("paintings.html", paintings = paintings.items, creators = all_creators, pagination = paintings, query=query, sort_by = sort_by)

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
    # TODO: need to get the user id from the session so that we can update the owner_id of the painting
    # can probably get the user id from the session by looking at the users table and finding the user with the email that is in the session
    # TODO: create a transaction in the transactions table every time a painting is bought
    # TODO: ask the user once they buy a painting if they want to keep it in the gallery. If not then viewable will be set to false and the painting will then have the requirements to be deleted from the database (sellable & viewable = false means the painting should be deleted)
    #might tweak this later
    painting = art_piece.query.get(piece_id)
    if painting and painting.sellable:
        painting.sellable = False
        db.session.commit()
        flash(f'Painting "{painting.title}" purchased successfully', 'success')
        return redirect(url_for('buy_menu'))
    else:
        flash('Painting not found or not sellable', 'danger')
        return "Painting not available for purchase", 404

#this is the main function that runs the app
if __name__ == '__main__':
    app.run(debug = True)

# Read creator function for display
def getcreator():
    query = select(creator)
    result = db.session.execute(query)

    creator_list = []
    for creators in result.scalars():
        creator_list.append((creators.creator_fname, creators.creator_lname, creators.birth_country, creators.birth_date, creators.death_date))
    return creator_list

# Function to get creator names mapped to IDs
def get_creator_names():
    query = select(creator)
    result = db.session.execute(query)
    
    creator_names = {}
    for creators in result.scalars():
        full_name = f"{creators.creator_fname} {creators.creator_lname}"
        creator_names[full_name] = creators.creator_id
    return creator_names

@app.route("/readcreator")
def readcreators():
    # Get all the creators using the getcreator function
    creator_list = getcreator()
    # Render the read creators page with all the required info
    return render_template("r_creator.html", creatorlist=creator_list)

# update creator function to allow modification 
@app.route("/updatecreator")
def updatecreators(feedback_message=None, feedback_type=False):
    creator_names = get_creator_names()
    return render_template("u_creator.html", 
                           creatornames=creator_names.keys(), 
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
    if creator_name in creator_names:
        creator_id = creator_names[creator_name]
    
    try:
        obj = db.session.query(creator).filter(
            creator.creator_id == creator_id).first()
        
        if obj is None:
            msg = 'Creator {} not found.'.format(creator_name)
            return updatecreators(feedback_message=msg, feedback_type=False)

        if creator_fname != '':
            obj.creator_fname = creator_fname
        if creator_lname != '':
            obj.creator_lname = creator_lname
        if birth_country != '':
            obj.birth_country = birth_country
        if birth_date != '':
            obj.birth_date = birth_date
        if death_date != '':
            obj.death_date = death_date

        db.session.commit()
    except Exception as err:
        db.session.rollback()
        return updatecreators(feedback_message=str(err), feedback_type=False)

    return updatecreators(feedback_message='Successfully updated creator {}'.format(creator_name),
                          feedback_type=True)

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

    try:
        entry = creator(creator_fname=creator_fname, creator_lname=creator_lname, birth_country=birth_country, birth_date=birth_date, death_date=death_date)
        db.session.add(entry)
        db.session.commit()
    except exc.IntegrityError as err:
        db.session.rollback()
        return createcreator(feedback_message='A creator named {} already exists. Create a creator with a different name.'.format(creator_fname), feedback_type=False)
    except Exception as err:
        db.session.rollback()
        return createcreator(feedback_message='Database error: {}'.format(err), feedback_type=False)

    return createcreator(feedback_message='Successfully added creator {}'.format(creator_fname),
                       feedback_type=True)

# create delete creator function 
@app.route("/deletecreator")
def deletecreator(feedback_message=None, feedback_type=False):
    creator_names = get_creator_names()
    return render_template("d_creator.html", 
                           creatornames=creator_names.keys(), 
                           feedback_message=feedback_message, 
                           feedback_type=feedback_type)

@app.route("/creatordelete", methods=['POST'])
def creatordelete():
    creator_name = request.form.get('creatornames')

    # if not request.form.get('confirmInput'):
    #     return deletecreator(feedback_message='Operation canceled. Creator not deleted.', feedback_type=False)
    
    creator_names = get_creator_names()
    if creator_name in creator_names:
        creator_id = creator_names[creator_name]
    else:
        return deletecreator(feedback_message='Creator not found.', feedback_type=False)

    try:
        obj = db.session.query(creator).filter(
            creator.creator_id == creator_id).first()
        
        if obj is None:
            msg = f'Creator {creator_name} not found.'
            return deletecreator(feedback_message=msg, feedback_type=False)
        
        db.session.delete(obj)
        db.session.commit()
    except Exception as err:
        db.session.rollback()
        return deletecreator(feedback_message=str(err), feedback_type=False)

    return deletecreator(feedback_message=f'Successfully deleted creator {creator_name}', feedback_type=True)

@app.route("/usercreate", methods=['get'])
def usercreate():
    fname = request.args.get('ufname')
    lname = request.args.get('ulname')
    email = request.args.get('email')
    pwd = request.args.get('password')
    role = request.args.get('role')
    msg = ''

    if fname and lname and pwd and role and email:
        existing_user = Users.query.filter_by(email=email).first()
        if existing_user:
            msg = 'Create failed: Email already exists.'
        else:
            new_user = Users(
                user_fname=fname,
                user_lname=lname,
                email=email,
                password=pwd,
                role=role
            )
            try:
                db.session.add(new_user)
                db.session.commit()
                msg = 'user create success'
            except:
                msg = 'Create Failed'
    else:
        msg = 'Create failed: missing input'

    return render_template('c_user.html', admin=session['admin'], msg=msg)

@app.route("/userread")
def userread():
    userlist = []
    if session['admin']:
        result = db.session.execute(select(Users))
    else:
        result = db.session.execute(select(Users).where(Users.user_id == session['user_id']))

    for users in result.scalars():
        userlist.append((users.user_fname, users.user_lname, users.email, users.password, users.role))    

    return render_template('r_user.html', userlist=userlist, admin=session['admin'])

@app.route("/userupdate", methods=['get'])
def userupdate():
    userlist = []
    if session['admin']:
        result = db.session.execute(select(Users))
    else:
        result = db.session.execute(select(Users).where(Users.user_id == session['user_id']))

    for users in result.scalars():
        userlist.append((users.user_fname, users.user_lname, users.email, users.password, users.role))  

    msg = get_flashed_messages()
    return render_template('u_user.html', msg=msg, userlist=userlist, admin=session['admin'])

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
            # Find the user by username (assuming `username` is a unique identifier)
            user_to_update = Users.query.filter_by(email=account).first()
            if user_to_update:
                msg = 'User update success'
                # Update user attributes if new values are provided
                if fname:
                    user_to_update.user_fname = fname
                if lname:
                    user_to_update.user_lname = lname
                if email:
                    existing_user = Users.query.filter_by(email=account).first()
                    if existing_user:
                        msg = 'Update failed: Email already exists.'
                    else:
                        user_to_update.email = email
                if pwd:
                    user_to_update.password = pwd
                if role:
                    user_to_update.role = role

                # Commit the changes to the database
                db.session.commit()
            else:
                msg = 'User update failed: No user with this username found.'
        except Exception as e:
            msg = f'User update failed: An error occurred. {str(e)}'
    else:
        msg = 'User update failed: Missing required fields or account identifier.'

    get_flashed_messages()
    flash(msg)
    return redirect("/userupdate")

@app.route("/userdelete", methods=['get'])
def userdelete():
    userlist = []
    if session['admin']:
        result = db.session.execute(select(Users))
    else:
        result = db.session.execute(select(Users).where(Users.user_id == session['user_id']))

    for users in result.scalars():
        userlist.append(users.email)  

    msg = get_flashed_messages()
 
    return render_template('d_user.html', userlist=userlist, msg=msg, admin=session['admin'])

@app.route("/userdelete_temp", methods=['get'])
def userdelete_temp():
    get_flashed_messages()
    email=request.args.get('useremail')

    if email or not email:
        try:
            user_to_delete = Users.query.filter_by(email=email).first()
            db.session.delete(user_to_delete)
            db.session.commit()
            flash('User delete success')

        except Exception:
            flash('User delete fail')
    return redirect("/userdelete")