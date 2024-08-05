from setup import *

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
            if(session['admin'] or buyer_id == session['user_id']):
                entry = transaction(piece_id=chosen_art_piece.piece_id, buyer_id=buyer_obj.user_id, seller_id=seller_obj.user_id, timestamp=timestamp)
                db.session.add(entry)
                chosen_art_piece.owner_id=buyer_obj.user_id
                db.session.commit()
            else:
               return createtransaction(feedback_message='You do not have permission to make this transaction {}'.format(title),
                    feedback_type=False) 
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



# create delete transaction function 
@app.route("/deletetransaction")
def deletetransaction(feedback_message=None, feedback_type=False):
    transaction_infos = get_transaction_info()
    return render_template("d_transaction.html", 
                           transactioninfos=transaction_infos.keys(), 
                           feedback_message=feedback_message, 
                           feedback_type=feedback_type)



@app.route("/transactiondelete", methods=['POST'])
def transactiondelete():
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

