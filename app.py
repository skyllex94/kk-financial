import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date
import re

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
# if not os.environ.get("API_KEY"):
#     raise RuntimeError("API_KEY not set")


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
    try:
        # stock_and_shares = db.execute(
        #     "SELECT type, symbol, SUM(shares) AS shares FROM purchases GROUP BY symbol")
        # for row in stock_and_shares:
        #     symbol = row["symbol"]
        #     row["cur_price"] = lookup(symbol)["price"]
        #     shares_total = shares_total + float(row["cur_price"])
        # row[symbol] = lookup(symbol)["name"]

        # Show all the positions owned with their current symbols and shares
        user_id = int(session["user_id"])
        positions = db.execute(
            "SELECT * FROM positions WHERE user_id = ?", user_id)

        # Print username next to the log out
        username = db.execute(
            "SELECT username FROM users WHERE id = ?", user_id)
        username = username[0]["username"].capitalize()

        total_price = 0
        for row in positions:
            # Add another row to the position dict to pass the current price of a stock
            symbol = row["symbol"]
            row["cur_price"] = lookup(symbol)["price"]

            # Sum of all the total prices of the stocks owned to calculate the total assets + cash
            price = float("{:.2f}".format(row["total_price"]))
            total_price += price

        cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)

        if len(cash) == 1:
            cash = cash[0]

            return render_template("index.html", positions=positions, cash=cash, total_price=total_price, username=username)

    except:
        return apology("Unable to load recent purchases")


@ app.route("/buy", methods=["GET", "POST"])
@ login_required
def buy():
    """Buy shares of stock"""
    # Get current user's name
    username = db.execute(
        "SELECT username FROM users WHERE id = ?", session["user_id"])
    username = username[0]["username"].capitalize()

    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("Please input a ticker symbol", 400)
        elif not request.form.get("shares"):
            return apology("Please input numbers of shares to buy", 400)

        # Check if the symbol inputted is valid and then proceed
        user_id = int(session["user_id"])
        symbol_check = request.form.get("symbol")
        shares = request.form.get("shares")

        if not symbol_check.isalpha():
            return apology("Enter only Alphabetical Character, please", 400)
        symbol_lookup = lookup(symbol_check)

        # Check if input value is not negative, fractional of alphabetical
        if (bool(re.match('^[0-9]*$', shares)) == False):
            return apology("Please only whole numbers for shares", 400)
        else:
            shares = int(shares)
            if shares < 0:
                return apology("Invalid number of shares", 400)

        # Check for successful API connection and return of a symbol
        if symbol_lookup == None:
            return apology("Incorrect ticker symbol", 400)

        total_amount = symbol_lookup["price"] * int(shares)
        time = date.today().strftime("%d/%m/%Y")
        cash_left = db.execute(
            "SELECT cash FROM users WHERE id = ?", user_id)

        if len(cash_left) == 1:
            cash_left = cash_left[0]["cash"]
            if total_amount <= cash_left:
                cash_left = cash_left - total_amount
                cash_left = float("{:.2f}".format(cash_left))
                total_amount = float("{:.2f}".format(total_amount))
                symbol = symbol_lookup["symbol"]
                name = symbol_lookup["name"]

                # Adjust the cash of the user after the purchase
                db.execute("UPDATE users SET cash = ? WHERE id = ?",
                           cash_left, user_id)

                # Insert and maniputale the "positions" database
                stock_check = db.execute(
                    "SELECT symbol FROM positions WHERE symbol = ? AND user_id = ?", symbol, user_id)

                if len(stock_check) == 0:
                    db.execute("INSERT INTO positions (user_id, symbol, name, shares, total_price) VALUES (?, ?, ?, ?, ?)",
                               user_id, symbol, name, shares, total_amount)
                else:
                    cur_shares = db.execute(
                        "SELECT shares FROM positions WHERE symbol = ? AND user_id = ?", symbol, user_id)
                    db.execute(
                        "UPDATE positions SET shares = ? WHERE symbol = ? AND user_id = ?", (cur_shares[0]["shares"] + int(shares)), symbol, user_id)
                    cur_pricetotal = db.execute(
                        "SELECT total_price FROM positions WHERE symbol = ? AND user_id = ?", symbol, user_id)

                    cur_price = float("{:.2f}".format(
                        cur_pricetotal[0]["total_price"]))
                    db.execute("UPDATE positions SET total_price = ? WHERE symbol = ? AND user_id = ?",
                               (cur_price + total_amount), symbol, user_id)

                # Insert and maniputale the "purchases" database responsible for the history of transactions
                db.execute("INSERT INTO purchases(user_id, shares, symbol, price_purchased, cash_left, time_purchased, type) VALUES(?, ?, ?, ?, ?, ?, ?)",
                           user_id, shares, symbol, total_amount, cash_left, time, 1)

                return render_template("inquiry.html", symbol_lookup=symbol_lookup, shares=shares, total_amount=total_amount, cash_left=cash_left, time=time, username=username)
            else:
                return render_template("buy.html", invalid=True, error_msg=usd(shares))

    return render_template("buy.html", username=username)


@ app.route("/history")
@ login_required
def history():
    """Show history of transactions"""
    try:
        # Fetch the username currectly logged
        user_id = int(session["user_id"])
        username = db.execute(
            "SELECT username FROM users WHERE id = ?", user_id)
        username = username[0]["username"].capitalize()

        rows = db.execute(
            "SELECT * FROM purchases WHERE user_id = ?", int(session["user_id"]))
        return render_template("history.html", rows=rows, username=username)

    except:
        return apology("Unable to load recent purchases")


@ app.route("/login", methods=["GET", "POST"])
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
        rows = db.execute("SELECT * FROM users WHERE username = ?",
                          request.form.get("username"))

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


@ app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    return redirect("/")


@ app.route("/quote", methods=["GET", "POST"])
@ login_required
def quote():
    """Get stock quote."""
    # Get the current user's name
    username = db.execute(
        "SELECT username FROM users WHERE id = ?", session["user_id"])
    username = username[0]["username"].capitalize()

    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("Please input a ticker symbol", 400)

        # Check if symbol is alphabetical
        symbol_check = request.form.get("symbol")
        if not symbol_check.isalpha():
            return apology("Enter only Alphabetical Character, please")

        symbol_lookup = lookup(symbol_check)
        # symbol = symbol_lookup["symbol"]
        if symbol_lookup == None:
            return apology("Incorrect ticker symbol")

        return render_template("quoted.html", symbol_lookup=symbol_lookup, username=username)
    else:
        return render_template("quote.html", username=username)


@ app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        if not request.form.get("username"):
            return apology("Username missing", 400)
        elif not request.form.get("password"):
            return apology("Missing password", 400)
        elif not request.form.get("confirmation") or (request.form.get("password") != request.form.get("confirmation")):
            return apology("Passwords not matching", 400)

        username = request.form.get("username")
        password = request.form.get("password")
        check_username = db.execute("SELECT username FROM users")
        for user in check_username:
            if str(user["username"]) == username:
                return apology("Username already taken, please try a different username")

        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)",
                   username, generate_password_hash(password))
        return redirect("/")

    return render_template("register.html")


@ app.route("/sell", methods=["GET", "POST"])
@ login_required
def sell():
    """Sell shares of stock"""
    user_id = int(session["user_id"])
    positions = db.execute(
        "SELECT * FROM positions WHERE user_id = ?", user_id)

    # Get current user's name
    username = db.execute(
        "SELECT username FROM users WHERE id = ?", session["user_id"])
    username = username[0]["username"].capitalize()

    if request.method == "POST":
        # Check if fields are populated
        if not request.form.get("symbol"):
            return apology("Please input a ticker symbol")
        elif not request.form.get("shares"):
            return apology("Please input numbers of shares to sell")

        # Check if the symbol inputted is valid and then proceed
        symbol_lookup = lookup(request.form.get("symbol"))
        if symbol_lookup == None:
            return apology("Incorrect ticker symbol", 400)

        # Check for a positive integer for shares
        shares = request.form.get("shares")

        # Check if input value is not negative, fractional of alphabetical
        if (bool(re.match('^[0-9]*$', shares)) == False):
            return apology("Please only whole numbers for shares", 400)
        else:
            shares = int(shares)
            if shares < 0:
                return apology("Invalid number of shares", 400)

        price = float("{:.2f}".format(symbol_lookup["price"]))
        total_amount = price * shares
        symbol = symbol_lookup["symbol"]
        time = date.today().strftime("%d/%m/%Y")

        # Adjust cash amount from the user
        cash = db.execute(
            "SELECT cash FROM users WHERE id = ?", user_id)

        if len(cash) == 1:
            # Add the cash to the user when selling
            cash = cash[0]["cash"]
            cash_addup = float("{:.2f}".format(cash + total_amount))
            db.execute("UPDATE users SET cash = ? WHERE id = ?",
                       cash_addup, user_id)

            # Insert and manipulate the "positions" database
            stock_check = db.execute(
                "SELECT symbol FROM positions WHERE symbol = ? AND user_id = ?", symbol, user_id)
            if len(stock_check) == 0:
                return apology("You do not have this stock to sell")
            else:
                cur_shares = db.execute(
                    "SELECT shares FROM positions WHERE symbol = ? AND user_id = ?", symbol, user_id)

                if cur_shares[0]["shares"] < shares:
                    return apology("You don't have this many shares of this stock to sell")
                elif cur_shares[0]["shares"] == shares:
                    db.execute(
                        "DELETE FROM positions WHERE symbol = ? AND user_id = ?", symbol, user_id)
                else:
                    db.execute(
                        "UPDATE positions SET shares = ? WHERE symbol = ? AND user_id = ?", (cur_shares[0]["shares"] - shares), symbol, user_id)
                    cur_pricetotal = db.execute(
                        "SELECT total_price FROM positions WHERE symbol = ? AND user_id = ?", symbol, user_id)

                    cur_price = float("{:.2f}".format(
                        cur_pricetotal[0]["total_price"]))

                    db.execute("UPDATE positions SET total_price = ? WHERE symbol = ? AND user_id = ?",
                               (cur_price - total_amount), symbol, user_id)

                # Insert information to the history of transactions database with type of sold
                db.execute(
                    "INSERT INTO purchases (user_id, shares, symbol, price_purchased, cash_left, time_purchased, type) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    user_id, shares, symbol, total_amount, cash_addup, time, 0)

                return render_template("inquiry.html", symbol_lookup=symbol_lookup, shares=shares, total_amount=total_amount,
                                       cash_left=cash_addup, time=time, username=username)

        else:
            return apology("Error with transaction occured", 400)

    else:
        return render_template("sell.html", positions=positions, username=username)
