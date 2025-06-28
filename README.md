# CSCE 310 Summer 2024 Database Systems Project (The Artfolio Gallery Application)
## Notice
This application was developed as a group project for CSCE 310 at Texas A&M University. The public URL is no longer supported.
Our application is hosted in the cloud using Heroku. You can access it by clicking [here](https://csce-310-artfolio-8885d6fafd86.herokuapp.com/).

## Requirements
- The only requirements someone will need to run this application are Python 3.8 or higher and Git. You can download Python from [here](https://www.python.org/downloads/) and Git from [here](https://git-scm.com/downloads).
  - External libraries are used in this application. However, further in the README are instructions on installing all these dependencies using Python and Git. 

## Useful Technologies used to develop the application (NOT NEEDED TO RUN THE APPLICATION)
- Tembo (used to host a Postgres database in the cloud) (https://tembo.io/)
- Heroku (used to host the application) (https://www.heroku.com/)
- Github (used to host the code and version control) (https://www.github.com/)

## Installation
Download the application code from Github using command:

`git clone https://github.com/Summer24-CSCE-310-Database-Systems/mvp-artfolio.git`

or

`git clone https://github.com/Summer24-CSCE-310-Database-Systems/mvp-artfolio/`

## Execute code
Run these commands in the terminal:

### Get all the dependencies
1. Create a virtual environment (name it whatever you want)
`python3 -m venv {name of virtual environment}`

2. Activate the virtual environment (for Mac/Linux/WSL)
`source {name of virtual environment}/bin/activate`

  if you are using Windows, use this command instead:

  `source {name of virtual environment}/Scripts/activate`

3. Install the dependencies
`pip install -r requirements.txt`

(Within the requirements.txt file, there are all the dependencies that are needed to run the application. Running the command above will install all these dependencies.)

### Run the application
Enter the following command in the terminal to run the application:
`flask run`

In the terminal, you should see a message that states the application is running on a local server. Copy the link and paste it into your browser to view the application.

![Flask Message](/static/images/readme_image1.png)

## Application Usage
Our application starts by greeting the user with a login page. Here is what that page looks like:
![Login Page](/static/images/login.png)

Here is the login information that both Professor Wade and TA Bengali can use to log in:

- Professor Wade
  - Email: paulinewade@tamu.edu
  - Password: password

- TA Bengali
  - Email: vendangibengali@tamu.edu
  - Password: password
 
- If curious about Patron view, you can use this login information:
  - Email: testuser@gmail.com
  - Password: password
    
    - This user has the role of Patron and can be used to test Patron capabilities rather than updating the information associated with your accounts.
   
- You can also create an account for the application if you are not already registered:
  - Simply click the button on the register button in the top right and you will be directed to a page where you can register for an account. This account will have the role of Patron and cannot be changed unless you ask an Admin to do so.
    ![Register for an Account](/static/images/register.png)
 
- Finally, if you do not wish to log in and rather want to look at the collection of paintings we have on display, you can click the view paintings button also located on the top right of the login page.
  ![Guest View of Paintings](/static/images/guest_view.png)

These pieces of login information are used purely to model the behavior of a user logging in. The application will not store any information associated with your email and will not use it for any purpose other than to log you in.

After logging in, the user will be taken to the main page of the application. From here, the application is pretty self-explanatory. Since both Professor Wade and TA Bengali have the same admin permissions, you have access to CRUD operations for all the entities in our application. You can create, read, update, and delete artworks, creators, users, and transactions.

Here is a showcase of the main page of the application:
![Main Page](/static/images/readme_image2.png)

An added feature of our application is the ability to buy paintings. You can click the "Buy A Painting" button on the bottom of the main page and view all sellable paintings. You can click on the "Buy" button to purchase a painting. A transaction will automatically be created and pushed to the database detailing who bought the painting and from who at what time. (keep in mind that only art pieces with the sellable attribute set to true will show up in the buy paintings page and after a painting is bought, the sellable attribute will be set to false)

Here is a showcase of the buy paintings page:
![Buy Paintings](/static/images/readme_image3.png)

Here is a showcase of the home page for admins:
![Admin Home](/static/images/readmeimage4.png)

Here is a showcase of the home page for patrons:
![Patron Home](/static/images/readmeimage5.png)

## Entity Specifications

### ERD (Entity Relationship Diagram)
![ERD](/static/images/erd.jpg)



### Art Piece
An art piece has the following attributes:
- ID (Primary Key) (auto-incremented)
  - Type: Integer (serial)
- Owner ID (Foreign Key) (gotten from the User entity, default is 1 which is the ID of the Artfolio Gallery)
  - Type: Integer
- Creator ID (Foreign Key) (gotten from the Creator entity)
  - Type: Integer
- Title
  - Type: String (100 characters)
- Year Finished
  - Type: Integer
- Cost
  - Type: Float
- Period (small description of the period the art piece was created in)
  - Type: String (200 characters)
- Photo link (link to the photo of the art piece)
  - Type: String (1000 characters)
- Sellable (boolean value that determines if the art piece is sellable)
  - Type: Boolean
- Viewable (boolean value that determines if the art piece is viewable)
  - Type: Boolean

#### Create
- A user can create an art piece by filling out all the attributes of the art piece with the exception of the ID since it is auto-incremented. The creator ID is inserted by selecting the creator's name from a dropdown list of all creators in the database. The owner ID is set to 1 by default since the Artfolio Gallery owns all the art pieces. Within the application, all information has to be filled out in order to create an art piece (other than the ones I mentioned above). Also, certain pieces of information have checks on them. For example, you can not input a string for the year finished or cost attributes. Similar checks are in place for the other inputted attributes as well.
- Here is a look at the create page for art pieces:
  ![Create a Painting](/static/images/create_painting.png)

#### Read
- A user sees all the viewable art pieces in the database by clicking on the "read artpiece" button on the home page. The viewable attribute of the art piece determines if the art piece shows up in the read artpiece page. The role of the user does not matter when viewing art pieces. The details of the art piece are displayed as well.
- Here is a look at the read page for art pieces:
  ![Search Feature for Art Pieces](/static/images/search_painting.png)

  ![Viewing a Painting and its information](/static/images/search_painting2.png)

#### Update
- A user can update an art piece by clicking on the "update artpiece" button on the home page. The user can only update an art piece that they own (if they are a patron) or any art piece (if they are an admin). The user can update all the attributes of the art piece with the exception of the ID since it is auto-incremented. The creator ID is inserted by selecting the creator's name from a dropdown list of all creators in the database. The main use of this page for a patron user will probably be to change the sellable attribute of the art piece they own.
- Here is a look at the update page for art pieces:
  ![Updating Paintings](/static/images/update_painting.png)  

#### Delete
- A user can delete an art piece by clicking on the "delete artpiece" button on the home page. The user can only delete an art piece that they own (if they are a patron) or any art piece (if they are an admin). Since deleting an art piece can mess up referential integrity, the application will not allow the user to delete an art piece that has been involved in a transaction (this is the only table that references the art piece table). If the user tries to delete an art piece that has been involved in a transaction, the application will display an error message. Otherwise, the art piece will be deleted from the database.
- Here is a look at the delete page for art pieces:
  ![Deleting Paintings](/static/images/delete_painting.png)

### Creator
A creator has the following attributes:
- ID (Primary Key) (auto-incremented)
  - Type: Integer (serial)
- Creator First Name
  - Type: String
- Creator Last Name
  - Type: String
- Birth Country
  - Type: String
- Birth Date
  - Type: Datetime
- Death Date
  - Type: Datetime
#### Create
- Both an admin and a patron can create a creator, whether through the "Create Creator" button in the home page or through the "Don't see your creator? Create a new one here." redirect link in the create artpiece page. Often times the birth date and death date of an artist are unknown, or they are alive, therefore there are checkboxes placed if the birth and death date values will be NULL. Checking the box will disable the calender input. 
#### Read
- Both admins and patrons can read the creators present in the databse. All the details of the creators are displayed in a table format in the app.
#### Update
- To maintian integrity and legitimacy of data, only admins are allowed to update/modify details of the creators. Patrons do not have access to the update creator page. 
#### Delete
- Only admins can delete creators from the database, patrons do not have access to this functionality. To avoid violation of refrential integrity, a creator cannot be deleted if they are associated with an artpiece in the database. To delete a creator, their artpiece has to be deleted from the database, and only then can the creator be deleted.

### User
A user has the following attributes:
- ID (Primary Key) (auto-incremented)
  - Type: Integer (serial)
- User First Name
  - Type: String
- User Last Name
  - Type: String
- Email (must be unique for all users)
  - Type: String
- Password
  - Type: String
- Role (1 character long)
  - Type: String
#### Create
New users may be created and are required to have values for all attributes, First name, Last name, Email, Password, and Role. Emails must be unique, you may not add a user who's email belongs to another user in the database. If you are logged in as an admin, you may create admin users. Patrons may only create other Patron users.
#### Read
Users have the ability to read all attributes of other users so long as they are logged in as an admin. Patron users may only view their own yser info.
#### Update
To update a users info, when changing their email, the same constraints occur where the new email cannot belong to an existing user. Admin users may update any users info. Patrons may only change their own. Patrons may not change their own role to Admin.
#### Delete
Deleting users is restricted to ensure refferential integrity. If a user is included in transaction, or art_piece entities, those entities must be deleted before the application will allow for that user to be deleted. Admins may delete any user given this constriant, Patrons may only delete their own account.

### Transaction
A transaction has the following attributes:
- ID (Primary Key) (auto-incremented)
  - Type: Integer (serial)
- Piece ID (Foreign Key) (gotten from the Art Piece entity)
  - Type: Integer
- Buyer ID (Foreign Key) (gotten from the User entity)
  - Type: Integer
- Seller ID (Foreign Key) (gotten from the User entity)
  - Type: Integer
- Timestamp (date where the transaction takes place)
  - Type: Datetime
#### Create
- Both an admin and a patron can create a transaction, whether through the "Create Transaction" button in the home page or through the "Buy" button in the buy menu page. The details of a transaction are chosen through drop down menus so that no invalid data can be inputted. A date is selected from a calendar or manually inputted.
#### Read
- A patron can only view a transaction that they participated in, whether they be a seller or a buyer in that transaction. Meanwhile, admins can view all transactions. The details of the transaction are displayed as well.
#### Update
- A patron can only update a transaction that they participated in, whether they be a seller or a buyer in that transaction. Meanwhile, admins can update all transactions. When a transaction's art piece is updated, the transaction's art piece changes, the updated art piece's owner id is updated to the transaction buyer, and the old art piece's owner id is updated to its original owner. When a transaction's buyer is updated, the transaction's art piece's owner is changed to the new buyer. When a transaction's seller is updated, the transaction's details are updated but that's it. Finally, when a transaction's date is updated, the transaction's details are updated but that's it.
#### Delete
- A patron can only update a transaction that they participated in, whether they be a seller or a buyer in that transaction. Meanwhile, admins can delete all transactions. When a transaction is deleted, the transaction's art piece's owner becomes the transaction's seller, returning the art piece's ownership to its former owner
