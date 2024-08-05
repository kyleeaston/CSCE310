# Written by Kyle Easton
from setup import *

@app.route("/usercreate", methods=['get'])
def usercreate():
    # Get message and feedback type
    msg = session.get('msg', None)
    successs = session.get('feedback_type', False)
    # Clear message and feedback_type
    try:
        session['feedback_type'] = False
        session.pop('msg')
    except:
        msg = None
    return render_template('c_user.html', admin=session['admin'], feedback_message=msg, feedback_type=successs)

@app.route("/usercreate_temp")
def usercreate_temp():
    # gather input
    fname = request.args.get('ufname')
    lname = request.args.get('ulname')
    email = request.args.get('email')
    pwd = request.args.get('password')
    role = request.args.get('role')

    #if no role is given, default to patron
    if not role:
        role = 'P'

    # Ensure all attributes are given
    if fname and lname and pwd and role and email:
        # Ensure unique email
        existing_user = users.query.filter_by(email=email).first()
        if existing_user:
            session['msg'] = 'Create failed: Email already exists.'
        else:
            # create new user
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

@app.route("/usercreate_guest", methods=['get'])
def usercreate_guest():
    # Get message and feedback type
    msg = session.get('msg', None)
    successs = session.get('feedback_type', False)
    # Clear message and feedback_type
    try:
        session['feedback_type'] = False
        session.pop('msg')
    except:
        msg = None
    return render_template('c_user_guest.html', admin=session['admin'], feedback_message=msg, feedback_type=successs)


@app.route("/usercreate_temp_guest")
def usercreate_temp_guest():
    # gather input
    fname = request.args.get('ufname')
    lname = request.args.get('ulname')
    email = request.args.get('email')
    pwd = request.args.get('password')
    role = request.args.get('role')

    #if no role is given, default to patron
    if not role:
        role = 'P'

    # Ensure all attributes are given
    if fname and lname and pwd and role and email:
        # Ensure unique email
        existing_user = users.query.filter_by(email=email).first()
        if existing_user:
            session['msg'] = 'Create failed: Email already exists.'
        else:
            # create new user
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
    return redirect('/usercreate_guest')

@app.route("/userread")
def userread():
    userlist = []
    # if logged in as admin: show all users
    # otherwise only show current user info
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
    # if admin: allow update of any user
    # if patron: only allow update of current user
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
    # gather input
    account=request.args.get('usernames')
    fname=request.args.get('ufname')
    lname=request.args.get('ulname')
    email=request.args.get('email')
    pwd=request.args.get('password')
    role=request.args.get('role')

    # ensure an account is selected, and an attribute has been input to update
    if account and (fname or lname or email or pwd or role):
        try:
            # ensure selected user exists
            user_to_update = users.query.filter_by(email=account).first()
            if user_to_update:
                session['msg'] = 'User update success'
                session['feedback_type'] = True
                # Ensure email is not duplicate
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
    email=request.args.get('useremail')

    if email:
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