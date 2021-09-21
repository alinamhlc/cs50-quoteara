import re
from tempfile import mkdtemp

import MySQLdb.cursors
from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   session)
from flask_mysqldb import MySQL
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import get_envvar, img_to_text, login_required, lookup

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Database connection
app.config['MYSQL_HOST'] = get_envvar('QUOTEARA_DB_HOST')
app.config['MYSQL_USER'] = get_envvar('QUOTEARA_DB_USER')
app.config['MYSQL_PASSWORD'] = get_envvar('QUOTEARA_DB_PASSWORD')
app.config['MYSQL_DB'] = get_envvar('QUOTEARA_DB')

# Intialize MySQL
mysql = MySQL(app)

@app.route("/")
def index():
    """"Show home page"""
    
    # Ensure user is logged in
    try:
        # Get all quotes the user has saved
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT books.book, quotes.quote from books, quotes WHERE books.id = quotes.book_id AND books.user_id = %s', (session["user_id"], ))

        # Save results as a list of dict
        quotes = []
        
        for row in cursor:
            # Look up book information based on id
            book = lookup(row["book"]) # there will be more el in the array with the same dict for title&author 
                                              # because this information is return for every quote from the db query
            book["quote"] = row["quote"]
            quotes.append(book)

        # Generate template
        return render_template("/index.html", quotes=quotes)

    except:
        return render_template("/index.html", quotes="")

@app.route("/addquote", methods=["GET", "POST"])
@login_required
def addquote():
    """"Add new quote"""
    
    # Ensure user is logged in
    try:
        # Get list of book id's
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT id, book FROM books WHERE user_id = %s', (session["user_id"], ))
        # Save results as a dict
        books = []
        for row in cursor:
            
            # Look up book information on Google Books based on book id 
            book = lookup(row["book"])

            # Add db id 
            book["book_id"]= row["id"]

            # Add results to list
            books.append(book)

        # Generate template
        return render_template("/addquote.html", books=books)

    except:
        return render_template("/addquote.html", books="")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    error = None

    # User reached route via POST
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirmation = request.form["confirmation"]
        email = request.form["email"]

        # Ensure fields are not empty
        if username and password and email and confirmation:

            # Check if username already exists exist
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM users WHERE username = %s', (username, ))
            account = cursor.fetchone()
            if account:
                error = "Account already exists"
            
            # Ensure valid email format
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                error = "Invalid email address"
            
            # Ensure username valid format
            elif not re.match(r'[A-Za-z0-9]+', username):
                error = "Username must contain only characters and numbers"
            
            # Ensure passwords match
            elif password != confirmation:
                error = "Passwords don't match"
            
            # Add user to db
            else:
                cursor.execute("INSERT INTO users VALUES (NULL, %s, %s, %s)", 
                    (username, generate_password_hash(password), email))
                mysql.connection.commit()
                # TODO: flash message does not show  
                # the session is cleared before log in (flash msg is saved there)
                flash("You are succesfully registered", "success")
                return redirect("/login")
        else:
            error = "All fields must be filled in"

    # User reached route via GET or POST was not succesfull
    return render_template("/register.html", error=error)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    error = None

    # Forget any user_id
    session.clear()

    # User reached route via POST
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            error = "Must provide username"
        
        # Ensure password was submitted
        elif not request.form.get("password"):
            error = "Must provide password"

        else: 
            # Query database for username
            username = request.form.get("username")
            password = request.form.get("password")
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM users WHERE username = %s', (username, ))
            account = cursor.fetchone()

            # Ensure username exists
            if not account:
                error = "Invalid username"
            
            # Ensure password is correct
            elif not check_password_hash(account["password"], password):
                error = "Invalid password"

            else:
                # Remember which user is logged in
                session["user_id"] = account["id"]

                # Redirect user to home page
                return redirect("/")
    
    # Add error to flash message
    if error:
        flash(error, "error")

    # User reached route via GET or POST was not succesfull
    return render_template("/login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Return user to index page
    return redirect("/")

@app.route("/addbook")
@login_required 
def addbook():
    """Search for books"""
    return render_template("/addbook.html")

@app.route("/processbook", methods=["POST"])
@login_required
def processbook():
    """Add book to the user's list"""
    book_id = request.form["book_id"]
    if book_id:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("INSERT INTO books VALUES (NULL, %s, %s)", 
                    (session["user_id"], book_id))
        mysql.connection.commit()

        # Open a file with access mode 'a'
        with open("sample.txt", "a") as file_object:
            # Append 'hello' at the end of file
            file_object.write(str(session["user_id"]) + " - " + book_id + "\n")

        return jsonify({'success' : 'Book added to your list'})

    return jsonify({'error' : 'Missing data!'})


@app.route("/processquote", methods=["POST"])
@login_required
def processquote():
    """Add quote to database"""

    book_id = request.form["book_id"]
    quote = request.form["quote"]
    if book_id:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("INSERT INTO quotes VALUES (NULL, %s, %s)", 
                    (book_id, quote))
        mysql.connection.commit()

        return jsonify({'success' : 'Quote added to your list'})

    return jsonify({'error' : 'Something went wrong. Missing data.'})


@app.route("/processPhoto", methods=["POST"])
def processPhoto():
    """Scan uploated photo and convert it to text"""
    
    img = request.files.to_dict(flat=True) #to_dict(flat=True) return the contents as regular dict, not ImmutableMultiDict
    
    # result of list(img)[0]] is the key of the first el
    # the value of this key, img[list(img)[0]]) is a FileStorage object  
    # Pillow can use FileStorage directly to read image, without saving to file
    # ref: https://stackoverflow.com/questions/65266569/how-can-i-open-an-image-of-filestorage-type-in-pillow

    quote = img_to_text(img[list(img)[0]])

    # Check if text was obtained
    if quote and not quote.isspace():
        return quote
    else:
        return "-1"



@app.route("/books")
@login_required
def books():
    """"Show list of user's books"""
    
    # Ensure user is logged in
    try:
    
        # Get list of book id's
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT book FROM books WHERE user_id = %s', (session["user_id"], ))
        # Save results as a dict
        books = []
        for row in cursor:
            # Get book id
            book_id = row["book"]
        
            # Look up book information based on id and add book to list
            books.append(lookup(book_id))

        # Generate template
        return render_template("/books.html", books=books)

    except:
        return render_template("/books.html", books="")


