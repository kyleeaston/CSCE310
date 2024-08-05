# ENTIRE FILE WRITTEN BY BLAKE DEJOHN

from setup import *

# Written by Blake Dejohn
@app.route('/paintings', methods = ['GET'])
def paintings():
    # get user info
    user_email = session.get('user_email')
    user = users.query.filter_by(email=user_email).first()
    user_role = user.role if user else None
    #used for page stuff
    page = request.args.get('page', 1, type=int)
    query = request.args.get('query', '', type=str)
    sort_by = request.args.get('sort_by', 'title', type=str)
    #can change this to whatever, decides how many paintings are shown per page
    per_page = 5

    #based on the user role, either show all paintings or only the ones that are viewable
    if user_role == 'A':
        if query:
            #filter based on what they searched for
            paintings_query = art_piece.query.filter(art_piece.title.ilike(f'%{query}%'))
        else:
            #else just get all the paintings
            paintings_query = art_piece.query
    else:
        # does the user want to search for a painting?
        if query:
            #filter based on what they searched for
            paintings_query = art_piece.query.filter(art_piece.title.ilike(f'%{query}%'), art_piece.viewable == True)
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

# Written by Blake Dejohn
@app.route('/paintings_guest', methods = ['GET'])
def paintings_guest():
    # get user info
    user_email = session.get('user_email')
    user = users.query.filter_by(email=user_email).first()
    user_role = user.role if user else None
    #used for page stuff
    page = request.args.get('page', 1, type=int)
    query = request.args.get('query', '', type=str)
    sort_by = request.args.get('sort_by', 'title', type=str)
    #can change this to whatever, decides how many paintings are shown per page
    per_page = 5

    #based on the user role, either show all paintings or only the ones that are viewable
    if user_role == 'A':
        if query:
            #filter based on what they searched for
            paintings_query = art_piece.query.filter(art_piece.title.ilike(f'%{query}%'))
        else:
            #else just get all the paintings
            paintings_query = art_piece.query
    else:
        # does the user want to search for a painting?
        if query:
            #filter based on what they searched for
            paintings_query = art_piece.query.filter(art_piece.title.ilike(f'%{query}%'), art_piece.viewable == True)
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
    return render_template("paintings_guest.html", paintings = paintings.items, creators = all_creators, owners=owners , pagination = paintings, query=query, sort_by = sort_by)

# Written by Blake Dejohn
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

# Written by Blake Dejohn
@app.route('/buy_painting/<int:piece_id>', methods = ['POST'])
def buy_painting(piece_id):
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

# Written by Blake Dejohn
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

# Written by Blake Dejohn
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

        if request.form.get('unknown_period'):
            period = 'Unknown'
        if request.form.get('unknown_title'):
            title = 'Unknown'

        #check if all the required fields are filled out
        if not title or not period or not cost or not photo_link or not year_finished:
            flash('Please fill out all fields', 'danger')
            return redirect(url_for('create_painting'))
        #create the painting
        new_painting = art_piece(owner_id=owner, creator_id=creator_id, title=title, year_finished=year_finished, period=period, cost=cost, photo_link=photo_link, sellable=sellable, viewable=viewable)

        try:
            #add the painting to the database
            db.session.add(new_painting)
            db.session.commit()
            flash(f'Painting "{title}" created successfully', 'success')
            return redirect(url_for('create_painting'))
        #if there is an error, rollback the changes and flash an error message
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating painting: {e}', 'danger')
            return redirect(url_for('create_painting'))
    #get all the creators so we can display them in the form
    creators = creator.query.all()
    #render the create painting page
    return render_template("c_painting.html", creators=creators)

# Written by Blake Dejohn
@app.route('/update_paintings', methods=['GET', 'POST'])
def update_paintings():
    if request.method == 'POST':
        try:
            #get the values from the form and update the painting
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
        #if there is an error, rollback the changes and flash an error message
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating painting: {e}', 'danger')
    #get all the paintings and creators so we can display them in the form
    user_email = session.get("user_email")
    user = users.query.filter_by(email=user_email).first()
    user_role = user.role if user else None
    user_id = user.user_id if user else None
    if user_role == 'A':
        paintings = art_piece.query.order_by(art_piece.piece_id).all()
    else:
        paintings = art_piece.query.filter_by(owner_id=user_id).order_by(art_piece.piece_id).all()
    creators = creator.query.all()
    #render the update paintings page
    return render_template("u_painting.html", paintings=paintings, creators=creators)