# Written by Adam Burhanpurwala
from setup import *

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
    creator_id = creator_names.get(creator_name)
    
    if not creator_id:
        return updatecreators(feedback_message=f'Creator {creator_name} not found.', feedback_type=False)
    
    try:
        obj = creator.query.filter_by(creator_id=creator_id).first()
        
        if not obj:
            return updatecreators(feedback_message=f'Creator {creator_name} not found.', feedback_type=False)

        if creator_fname:
            if not creator_fname.strip():
                return updatecreators(feedback_message='First name cannot be empty.', feedback_type=False)
            obj.creator_fname = creator_fname

        if creator_lname:
            if not creator_lname.strip():
                return updatecreators(feedback_message='Last name cannot be empty.', feedback_type=False)
            obj.creator_lname = creator_lname

        if birth_country:
            if not birth_country.strip():
                return updatecreators(feedback_message='Birth country cannot be empty.', feedback_type=False)
            obj.birth_country = birth_country

        # Ensure birth date is older than death date
        if birth_date and death_date:
            try:
                birth_date_obj = datetime.strptime(birth_date, '%Y-%m-%d')
                death_date_obj = datetime.strptime(death_date, '%Y-%m-%d')
                if birth_date_obj >= death_date_obj:
                    return updatecreators(feedback_message='Birth date must be older than death date.', feedback_type=False)
            except ValueError:
                return updatecreators(feedback_message='Invalid date format. Please use YYYY-MM-DD.', feedback_type=False)

        if birth_date:
            obj.birth_date = birth_date

        if death_date:
            obj.death_date = death_date

        db.session.commit()
        return updatecreators(feedback_message=f'Successfully updated {creator_name}', feedback_type=True)
    except Exception as err:
        db.session.rollback()
        return updatecreators(feedback_message=str(err), feedback_type=False)
        
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

    # Check if first name, last name, or birth country is empty
    if not creator_fname:
        return createcreator(feedback_message='First name is required.', feedback_type=False)
    
    if not creator_lname:
        return createcreator(feedback_message='Last name is required.', feedback_type=False)
    
    if not birth_country:
        return createcreator(feedback_message='Birth country is required.', feedback_type=False)

    # Handle optional birth date
    if nobdate == 'on':
        birth_date = None
    elif not birth_date:
        return createcreator(feedback_message='Birth date is required unless "Unknown Birth Date" is checked.', feedback_type=False)

    # Handle optional death date
    if ifalive == 'on':
        death_date = None
    elif not death_date:
        return createcreator(feedback_message='Death date is required unless "Unknown or Alive" is checked.', feedback_type=False)

    # Check if a creator with the same first name and last name already exists
    existing_creator = db.session.query(creator).filter_by(
        creator_fname=creator_fname, creator_lname=creator_lname).first()

    if existing_creator:
        return createcreator(feedback_message=f'A creator named {creator_fname} {creator_lname} already exists.', feedback_type=False)

    # Ensure birth date is older than death date
    if birth_date and death_date:
        try:
            birth_date_obj = datetime.strptime(birth_date, '%Y-%m-%d')
            death_date_obj = datetime.strptime(death_date, '%Y-%m-%d')
            if birth_date_obj >= death_date_obj:
                return createcreator(feedback_message='Birth date must be older than death date.', feedback_type=False)
        except ValueError:
            return createcreator(feedback_message='Invalid date format. Please use YYYY-MM-DD.', feedback_type=False)

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
    
    creator_names = get_creator_names()
    creator_id = creator_names.get(creator_name)

    if not creator_id:
        return deletecreator(feedback_message=f'{creator_name} not found.', feedback_type=False)

    try:
        obj = creator.query.filter_by(creator_id=creator_id).first()
        
        if not obj:
            return deletecreator(feedback_message=f'{creator_name} not found.', feedback_type=False)
        
        # Check if the creator is associated with any art pieces
        associated_art_pieces = db.session.query(art_piece).filter_by(creator_id=creator_id).all()
        if associated_art_pieces:
            return deletecreator(feedback_message=f'{creator_name} is associated with an art piece, and cannot be deleted.', feedback_type=False)

        db.session.delete(obj)
        db.session.commit()
        return deletecreator(feedback_message=f'Successfully deleted {creator_name}', feedback_type=True)
    except Exception as err:
        db.session.rollback()
        return deletecreator(feedback_message=f'Database error: {err}', feedback_type=False)
