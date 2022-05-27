
# you import the Flask class and the render_template() function from the flask package.
#You use the Flask class to create your Flask application instance app = Flask(__name__)
#Then you define a view function (which is a Python function that returns an HTTP response) def quote():
#using the @app.route("/quote", methods=["GET", "POST"])  decorator, which converts a regular function into a view function.
#This view function uses the render_template() function to render a template file called quote.html.

import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import datetime
import pytz

from helpers import apology, login_required, lookup, usd

# export API_KEY=pk_d95df862df7848a38e10b1f080300e5e

# Configure application to be a flask app
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies) (Storing a user)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_id = session["user_id"]
    #we are going to store the user_id from the session into a variable called userid
    #The session is the interval at which the client logs on to the server and logs out the server.
    transactions_db = db.execute("SELECT symbol, SUM(shares) AS shares, price FROM Transactions WHERE user_id = ? GROUP BY symbol", user_id)
    #we create a variable that executes a sql function. The function looks up the symbol for the shares and adds the number of shares.
    #using the AS command we create an alias for the calc called "shares. GROUP BY finds the number of shares in each symbol".
    cash_db = db.execute("SELECT cash FROM users WHERE id = ?", user_id) #We go into users database and we find cash.
    cash = cash_db[0]["cash"]
    #This will bring up a dictionary with the name cash and the actual cash number.  [{"cash:10000"}]
    #To turn this into a real number so we get the first element of the list using the KEY "cash"

    return render_template("index.html", database = transactions_db, cash = cash)
    #We display this in a table



@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("buy.html")

    else:
        symbol = request.form.get("symbol") #left is the variable from python and right is the variable from html
        shares = int(request.form.get("shares")) #We need to make sure that an int is returned to us

        if not symbol: #if there is no input, return the apology
            return apology("Enter symbol again")
        #def lookup(symbol): function contacts the API URL and fetches the content using quote = response.json()
        #We need to create a variable that will be the capitilized symbol that the api can look it up

        if not shares: #if there is no input, return the apology
            return apology("Enter shares")

        stock = lookup(symbol.upper()) #The lookup function returns a dictionary with keys name,price.symbol

        #  If there is a problem with the lookup function it will return None and so if this happens, return apology
        if stock == None:
            return apology("Symbol does not exist")

        if shares < 0:
            return apology("Enter a positive number ")
        # From the dictionary within the variable stock we find the float value of price and multiply with shares
        transaction_value = shares * stock["price"]

        user_id = session["user_id"]
        #we are going to store the user_id from the session into a variable called userid
        #The session is the interval at which the client logs on to the server and logs out the server.
        user_cash_db = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
        #This will bring up a dictionary with the name cash and the actual cash number.  [{"cash:10000"}]
        #To turn this into a real number so we get the first element of the list using the KEY "cash"
        user_cash = user_cash_db[0]["cash"]

        if user_cash < transaction_value:
            return apology("Not enough cash")

        acc_bal = user_cash - transaction_value
        #UPDATE Customers
        #SET ContactName = 'Alfred Schmidt', City= 'Frankfurt'
        #WHERE CustomerID = 1;
        # each ? will be filled with the variables in order left to right

        date = datetime.datetime.now(pytz.timezone("Asia/Tokyo"))

        db.execute("UPDATE users SET cash = ? WHERE id = ?", acc_bal, user_id)

        db.execute("INSERT INTO Transactions (user_id,symbol,shares,price,date,Total_price) VALUES(?,?,?,?,?,?)", user_id, symbol.upper(), shares, stock["price"], date,transaction_value  )
        #adds a new row in sql from python is each place name, month, day

        flash("Transaction Complete")
        return redirect("/")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    user_id = session["user_id"]
    #we are going to store the user_id from the session into a variable called userid
    #The session is the interval at which the client logs on to the server and logs out the server.
    transactions_db = db.execute("SELECT* FROM transactions WHERE user_id = ?", user_id )
     # we need to display what lookup function returns as html.
    #Templates are files that contain static data as well as placeholders for dynamic data.
    return render_template("history.html", transactions =  transactions_db)
    #when we send data to html we have to have different notation from html and sql


@app.route("/transfer", methods=["GET", "POST"])
@login_required
def transfer():
    """Transfer cash"""
    user_id = session["user_id"]
    #we are going to store the user_id from the session into a variable called userid
    #The session is the interval at which the client logs on to the server and logs out the server.
    if request.method == "GET":
        return render_template("transfer.html")
    else:
        transfer = int(request.form.get("transfer")) #left is the variable from python and right is the variable from html

        if not transfer: #if there is no input, return the apology
            return apology("Enter amount again")
        #def lookup(symbol): function contacts the API URL and fetches the content using quote = response.json()
        #We need to create a variable that will be the capitilized symbol that the api can look it up

    if transfer > 100000 :
            return apology("Maximum is 100K ")

    else:

        user_cash_db = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
        #This will bring up a dictionary with the name cash and the actual cash number.  [{"cash:10000"}]
        #To turn this into a real number so we get the first element of the list using the KEY "cash"
        user_cash = user_cash_db[0]["cash"]

        if (-1)*user_cash > transfer :
            return apology("Not enough cash ")

        new_bal = user_cash + transfer

        date = datetime.datetime.now(pytz.timezone("Asia/Tokyo"))

        db.execute("UPDATE users SET cash = ? WHERE id = ?", new_bal, user_id)

        return redirect("/")



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required

def quote():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html")

    else:
        symbol = request.form.get("symbol") #left is the variable from python and right is the variable from html

        if not symbol: #if there is no input, return the apology
            return apology("Enter symbol again")
        #def lookup(symbol): function contacts the API URL and fetches the content using quote = response.json()
        #We need to create a variable that will be the capitilized symbol that the api can look it up

        stock = lookup(symbol.upper()) #The lookup function returns a dictionary with keys name,price.symbol

        #  If there is a problem with the lookup function it will return None and so if this happens, return apology
        if stock == None:
            return apology("Enter symbol again")

        # we need to display what lookup function returns as html.
        #Templates are files that contain static data as well as placeholders for dynamic data.
        return render_template("quoted.html", name = stock["name"], price = stock["price"], symbol = stock["symbol"])



@app.route("/register", methods=["GET", "POST"])#GET is used for viewing something, without changing it, while POST is used for changing something
def register():
    if request.method == "GET":

        return render_template("register.html") #todo

    else:
        # TODO: Add the user's entry into the database
        username = request.form.get("username") #left is the variable from python and right is the variable from html
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")


        """Register user"""
        if not username: #if we already have the username or there is no input, return the apology
            return apology("Enter username again")

        if not password: #if we already have the username or there is no input, return the apology
            return apology("Enter password again")

        if not confirmation: #if we already have the username or there is no input, return the apology
            return apology("Enter confirmation again")

        if password != confirmation:
            return apology ("Passwords do not match")

        hash = generate_password_hash(password) #This command via Import at the top. This "randomizes" a password and we store it in a variable "password"
        #We need to
        try: #The try block lets you test a block of code for errors.
          #insert into the sql data base called users. In the rows we populate username and hash
            new_user = db.execute("INSERT INTO users (username, hash) VALUES(?,?)", username, hash) #adds a new row in sql from python is each place name, month, day
        #Each question mark is a placeholder for the actual data we will put in name, month day
        except:#The except block lets you handle the error.
            return apology("Username Taken")

        session["userid"] = new_user #The session is the interval at which the client logs on to the server and logs out the server.

        return redirect("/")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "GET":

        user_id = session["user_id"]
        #we are going to store the user_id from the session into a variable called userid
        #The session is the interval at which the client logs on to the server and logs out the server.

        symbol_db = db.execute("SELECT symbol FROM Transactions WHERE user_id = ? GROUP BY symbol HAVING SUM(shares) > 0", user_id)
        #HAVING clause was added to SQL because the WHERE keyword cannot be used with aggregate functions.
        #using the AS command we create an alias for the calc called "shares. GROUP BY finds the number of shares in each symbol".

        return render_template("sell.html", symbol_list = [row["symbol"] for row in symbol_db])

    else:

        symbol = request.form.get("symbol") #left is the variable from python and right is the variable from html
        shares = int(request.form.get("shares")) #We need to make sure that an int is returned to us

        if not symbol: #if there is no input, return the apology
            return apology("Enter symbol again")
        #def lookup(symbol): function contacts the API URL and fetches the content using quote = response.json()
        #We need to create a variable that will be the capitilized symbol that the api can look it up

        if not shares: #if there is no input, return the apology
            return apology("Enter shares")

        stock = lookup(symbol.upper()) #The lookup function returns a dictionary with keys name,price.symbol

        #  If there is a problem with the lookup function it will return None and so if this happens, return apology
        if stock == None:
            return apology("Symbol does not exist")

        if shares < 0:
            return apology("Enter a positive number ")
        # From the dictionary within the variable stock we find the float value of price and multiply with shares
        transaction_value = shares * stock["price"]

        user_id = session["user_id"]
        #we are going to store the user_id from the session into a variable called userid
        #The session is the interval at which the client logs on to the server and logs out the server.
        user_cash_db = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
        #This will bring up a dictionary with the name cash and the actual cash number.  [{"cash:10000"}]
        #To turn this into a real number so we get the first element of the list using the KEY "cash"
        user_cash = user_cash_db[0]["cash"]

        acc_bal = user_cash + transaction_value # We now will add the cash value of the stock back

        user_shares = db.execute("SELECT shares FROM Transactions WHERE user_id = ? AND symbol = ? GROUP BY symbol", user_id, symbol)
        #user_id needs to match the column in Transactions

        user_shares_real = user_shares[0]["shares"]

        if shares > user_shares_real:
            return apology("No shares ")

        date = datetime.datetime.now(pytz.timezone("Asia/Tokyo"))

        db.execute("UPDATE users SET cash = ? WHERE id = ?", acc_bal, user_id)

        db.execute("INSERT INTO Transactions (user_id,symbol,shares,price,date,Total_price) VALUES(?,?,?,?,?,?)", user_id, symbol.upper(), (-1)*shares, stock["price"], date,transaction_value  )
        #adds a new row in sql from python but this time the number of shares we enter will get subtracted

        flash("Transaction Complete")
        return redirect("/")

