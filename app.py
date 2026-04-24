import io
from datetime import timedelta, date, datetime
from PIL import Image
from helpers import apology, login_required
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for, send_file, jsonify, send_from_directory
from flask_session import Session
import json
from werkzeug.security import check_password_hash, generate_password_hash
import pytz

est = pytz.timezone('America/New_York')
app = Flask(__name__)

# Configure session
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:////home/jaxeuseuse/ClargClick/clargclick.db")

def human_format(num):
    if num is None: return "0"

    try:
        num = float(num)
    except (ValueError, TypeError):
        return str(num)

    magnitude = 0
    # Full names for Short Scale numeration
    suffixes = [
        '', ' Thousand', ' Million', ' Billion', ' Trillion', ' Quadrillion',
        ' Quintillion', ' Sextillion', ' Septillion', ' Octillion', ' Nonillion',
        ' Decillion', ' Undecillion', ' Duodecillion', ' Tredecillion',
        ' Quattuordecillion', ' Quindecillion', ' Sexdecillion',
        ' Septendecillion', ' Octodecillion', ' Novemdecillion',
        ' Vigintillion', ' Unvigintillion', ' Duovigintillion',
        ' Trevigintillion', ' Quattuorvigintillion', ' Quinvigintillion',
        ' Sexvigintillion', ' Septenvigintillion', ' Octovigintillion',
        ' Novemvigintillion', ' Trigintillion', ' Untrigintillion',
        ' Duotrigintillion', ' Tretrigintillion', ' Quattuortrigintillion',
        ' Quintrigintillion', ' Sextrigintillion'
    ]

    max_magnitude = len(suffixes) - 1

    # Logic to reduce the number and find the correct name
    while abs(num) >= 1000 and magnitude < max_magnitude:
        magnitude += 1
        num /= 1000.0

    # Force dot decimal and remove trailing zeros
    formatted_num = "{:.2f}".format(num).rstrip('0').rstrip('.')

    return f"{formatted_num}{suffixes[magnitude]}"
app.jinja_env.filters['humanize'] = human_format

# Define clargs and their initial states
clargs_data = {
    "clarg": {"unlocked": True, "selected": False},
    "dr_clarg": {"unlocked": False, "selected": False},
    "business_clarg": {"unlocked": False, "selected": False},
    "vacation_clarg": {"unlocked": False, "selected": False},
    "jamaican_clarg": {"unlocked": False, "selected": False},
    "ben_clarg": {"unlocked": False, "selected": False}
}


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/clargclick", methods=["GET", "POST"])
def index():
    """Play the game and display leaderboard"""
    if request.method == "POST":
        # Handle game result submission via AJAX (only for logged-in users)
        if "user_id" in session:
            data = request.get_json()
            cps = float(data["cps"])
            clicks = float(data["clicks"])
            user_id = int(session["user_id"])

            current_clicks = db.execute("SELECT clicktotal FROM users WHERE id = ?", user_id)
            if current_clicks:
                if current_clicks[0]["clicktotal"] is None:
                    current_clicks = clicks
                else:
                    current_clicks = current_clicks[0]["clicktotal"] + clicks
            else:
                current_clicks = clicks

            db.execute("UPDATE users SET clicktotal = ? WHERE id = ?", current_clicks, user_id)

            personal_clarg = db.execute(
                "SELECT clargs_owned FROM users WHERE id = ?",
                user_id
            )

            # Get the actual clarg type string
            selected_clarg = get_selected_clarg(personal_clarg)[0]['clargtype']

            # Check for existing score and update if new score is higher
            existing_score = db.execute(
                "SELECT cps FROM scores WHERE user_id = ? ORDER BY cps DESC LIMIT 1",
                user_id
            )
            if existing_score:
                if cps > existing_score[0]["cps"]:
                    try:
                        db.execute(
                            "UPDATE scores SET cps = ?, clarg_used = ? WHERE user_id = ?",
                            cps, selected_clarg, user_id
                        )
                        return jsonify({"message": "Score updated successfully!"})
                    except Exception as e:
                        print(f"Error updating score: {e}")
                        return jsonify({"error": "Failed to update score"}), 500
                else:
                    return jsonify({"message": "Score not higher than existing score."})
            else:
                # Insert new score if no existing score
                try:
                    db.execute(
                        "INSERT INTO scores (user_id, cps, clarg_used) VALUES (?, ?, ?)",
                        user_id, cps, selected_clarg
                    )
                    return jsonify({"message": "Score submitted successfully!"})
                except Exception as e:
                    print(f"Error inserting score: {e}")
                    return jsonify({"error": "Failed to insert score"}), 500

        else:
            # No score stored for guest users
            return jsonify({"message": "Guest scores are not recorded."})

    else:
        # Fetch the top 5 scores (only for registered users)
        top_5 = fetch_top_5()

        # Fetch user's selected clarg and personal best (handle guests)
        if "user_id" in session:
            user_id = session["user_id"]
            personal_clarg = db.execute(
                "SELECT clargs_owned FROM users WHERE id = ?",
                user_id
            )
            selected_clarg = get_selected_clarg(personal_clarg)

            # Get personal best only for logged-in users
            personal_best = get_personal_best(user_id)
        else:
            selected_clarg = [{"clargtype": "clarg"}]  # Default clarg for guests
            personal_best = None  # No personal best for guests

        # Check if the user is logged in
        logged_in = "user_id" in session
       # show today's suggestions
        today = date.today().isoformat()
        suggestions = db.execute(
            "SELECT id, username, text, submitted_date, timestamp FROM suggestions WHERE submitted_date = ? ORDER BY id DESC",
            today,
        )

        return render_template(
            "index.html",
            top5=top_5,
            personal=personal_best,  # Pass personal_best to the template
            logged_in=logged_in,
            personal_clarg=selected_clarg,
            suggestions=suggestions
        )


def fetch_top_5():
    """Helper function to fetch top 5 scores with user details."""
    top_5_scores = db.execute("""
        SELECT u.name, s.cps, u.profile_picture, u.id AS user_id, s.clarg_used
        FROM scores s
        JOIN users u ON s.user_id = u.id
        ORDER BY s.cps DESC
        LIMIT 5
    """)

    for score in top_5_scores:
        # No need to calculate clarg from clargs_owned anymore
        score["clarg"] = score["clarg_used"]  # Use the value from the scores table directly

    return top_5_scores

#gemini's work mostly maybe 30%
def get_selected_clarg(clargs_owned_json):
    """Helper function to determine the selected clarg."""
    if clargs_owned_json and clargs_owned_json[0]["clargs_owned"]:
        clargs_owned = json.loads(clargs_owned_json[0]["clargs_owned"])
        for clarg_type, data in clargs_owned.items():
            if data["selected"]:
                return [{"clargtype": clarg_type}]
    return [{"clargtype": "clarg"}]  # Default clarg


def get_personal_best(user_id):
    """Helper function to get personal best score and rank."""
    if user_id is None:
        return None

    personal_best_query = """
        SELECT MAX(s.cps) AS cps, u.name, u.profile_picture, s.clarg_used,
               (SELECT COUNT(*) + 1 FROM scores WHERE cps > MAX(s.cps)) AS rank
        FROM scores s
        JOIN users u ON s.user_id = u.id
        WHERE s.user_id = ?
    """
    personal_best = db.execute(personal_best_query, user_id)

    if personal_best and personal_best[0]["cps"] is not None:
        # Use the clarg_used from the scores table
        personal_best[0]["clarg"] = personal_best[0]["clarg_used"]
        personal_best[0]["pfp"] = url_for('profile_picture', user_id=user_id)
        return personal_best[0]
    else:
        # Handle users who have no scores yet
        return {
            "cps": 0,
            "name": db.execute("SELECT name FROM users WHERE id = ?", user_id)[0]["name"],
            "clarg": get_selected_clarg(db.execute("SELECT clargs_owned FROM users WHERE id = ?", user_id))[0]['clargtype'],
            "rank": "Unranked",
            "pfp": url_for('profile_picture', user_id=user_id)
        }


@app.route("/clargclick/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Validate form inputs
        if not request.form.get("name"):
            return apology("must provide name", 400)
        elif not request.form.get("password"):
            return apology("must provide password", 400)
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords must match", 400)

        # Get uploaded profile picture
        profile_picture = request.files.get("profile_picture")
        # pulled from Gemini
        if profile_picture:
            # Convert the uploaded image to binary data
            profile_picture_data = convertToBinaryData(profile_picture)
        else:
            # Use default profile picture if none uploaded
            with open("/home/jaxeuseuse/ClargClick/static/default.png", "rb") as default_img:
                profile_picture_data = default_img.read()

        # Generate password hash
        password_hash = generate_password_hash(request.form.get("password"))

        # Initialize clargs_owned with default values
        clargs_owned_json = json.dumps(clargs_data)
        clicktotal = 0
        # Insert user and profile picture into the database
        try:
            insert_user_with_image(
                request.form.get(
                    "name"), password_hash, profile_picture_data, clargs_owned_json, clicktotal
            )
            # Retrieve the user_id from the database
            user_id = db.execute("SELECT id FROM users WHERE name = ?",
                                 request.form.get("name"))[0]["id"]

            # Save the user_id in the session
            session["user_id"] = user_id
            session["first_login"] = True
            return redirect("/clargclick")
        except Exception as e:
            print(f"Error during registration: {e}")
            return apology("Registration failed", 400)

    return render_template("register.html")


@app.route("/clargclick/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("name"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE name = ?", request.form.get("name")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
                rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        session["first_login"] = True
        return redirect("/clargclick")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/clargclick/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/clargclick")

#tanks to chagpt for this library knowledge and half the code
def convertToBinaryData(image_file):
    """Convert image file to binary PNG data."""
    try:
        # Open the image file using PIL
        img = Image.open(image_file)

        # Convert image to PNG format in memory
        img_converted = io.BytesIO()
        img.save(img_converted, format="PNG")  # Save image as PNG format

        # Return the binary data
        return img_converted.getvalue()
    except Exception as e:
        print(f"Error converting image to binary: {e}")
        return None

#thanks to chagpt
def insert_user_with_image(name, password_hash, profile_picture_data, clargs_owned_json, clicktotal):
    """Insert user data and profile picture as a BLOB into the database."""
    try:
        # Insert the user's name, password hash, and image data into the database
        db.execute("""
        INSERT INTO users (name, hash, profile_picture, clargs_owned, clicktotal)
        VALUES (?, ?, ?, ?, ?)
        """, name, password_hash, profile_picture_data, clargs_owned_json, clicktotal)
        print("User and image inserted successfully")
    except Exception as e:
        print(f"Failed to insert user data into the database: {e}")
        return None


@app.route("/clargclick/profile_picture/<int:user_id>")
def profile_picture(user_id):
    """Serve the profile picture from the database."""
    try:
        # Fetch the user's profile picture from the database
        user = db.execute("SELECT profile_picture FROM users WHERE id = ?", user_id)

        if user and user[0]["profile_picture"]:
            # Serve the user's profile picture
            profile_picture_data = user[0]["profile_picture"]
            return send_file(io.BytesIO(profile_picture_data), mimetype="image/png")
        else:
            # Serve the default profile picture if none is found
            return send_file("/home/jaxeuseuse/ClargClick/static/default.png", mimetype="image/png")
    except Exception as e:
        print(f"Error serving profile picture: {e}")
        # Return default picture if there is an error
        return send_file("/home/jaxeuseuse/ClargClick/static/default.png", mimetype="image/png")


@app.route("/clargclick/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    # Fetch user details
    user_id = session.get("user_id")
    rows = db.execute("SELECT name, clargs_owned FROM users WHERE id = ?", user_id)
    username = rows[0]["name"]

    # Parse the user's clargs
    clargs_owned_json = rows[0]["clargs_owned"]
    clargs_owned = json.loads(clargs_owned_json)
    clargs_owned_raw = clargs_owned_json
    try:
        # Try to parse it as JSON
        if isinstance(clargs_owned_raw, str):
             clargs_owned = json.loads(clargs_owned_raw)
        else:
             # It might already be a dictionary if the DB driver converted it
             clargs_owned = clargs_owned_raw

    except (json.JSONDecodeError, TypeError):
        # If the manual data is garbage, fallback to defaults so the site loads
        print("Error parsing JSON, using defaults")
        clargs_owned = clargs_data # using your default variable from top of app

    # Now continue...
    clargs_count = sum(1 for clarg in clargs_owned.values() if clarg["unlocked"])


    # Calculate the user's rank
    rank_query = """
    SELECT COUNT(*) + 1 AS rank
    FROM scores
    WHERE cps > (
        SELECT MAX(cps)
        FROM scores
        WHERE user_id = ?
    )
    """
    rank_result = db.execute(rank_query, user_id)
    leaderboard_place = rank_result[0]["rank"] if rank_result else "Unranked"

    # Ensure "Unranked" is shown if the user has no scores
    user_high_score_query = "SELECT MAX(cps) AS max_score FROM scores WHERE user_id = ?"
    user_high_score_result = db.execute(user_high_score_query, user_id)
    # Corrected line
    user_high_score = user_high_score_result[0]["max_score"] if user_high_score_result else 0
    if not user_high_score:
        leaderboard_place = "Unranked"

    # Get the list of available clargs for the dropdown
    available_clargs = list(clargs_data.keys())
    click_total = db.execute("SELECT clicktotal FROM users WHERE id = ?", user_id)[0]['clicktotal']
    return render_template(
        "dashboard.html",
        username=username,
        clargs_count=clargs_count,
        leader_board_number=leaderboard_place,
        clargs_owned=clargs_owned,
        available_clargs=available_clargs,
        click_total=click_total
    )


@app.route("/clargclick/select_clarg", methods=["POST"])
@login_required
def select_clarg():
    """Handle Clarg selection."""
    selected_clarg = request.form.get("selected_clarg")
    user_id = session.get("user_id")

    # Fetch the current clargs_owned data
    current_clargs_owned = db.execute("SELECT clargs_owned FROM users WHERE id = ?", user_id)[
        0]["clargs_owned"]
    clargs_owned = json.loads(current_clargs_owned)

    # Check if the selected Clarg is unlocked
    if clargs_owned[selected_clarg]["unlocked"]:
        # Update the selected status only if unlocked
        for clarg_type in clargs_owned:
            clargs_owned[clarg_type]["selected"] = (clarg_type == selected_clarg)

        # Update the database with the new selected Clarg
        db.execute("UPDATE users SET clargs_owned = ? WHERE id = ?",
                   json.dumps(clargs_owned), user_id)

        return redirect(url_for("index"))
    else:
        # If the Clarg is locked, do nothing and redirect
        return None


@app.route("/clargclick/new_password", methods=["POST"])
@login_required
def change_password():
    """Allow users to change their password"""
    user_id = session.get("user_id")
    current_password = request.form.get("password")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")

    # Ensure current password is correct
    rows = db.execute("SELECT hash FROM users WHERE id = ?", user_id)
    if len(rows) != 1 or not check_password_hash(rows[0]["hash"], current_password):
        flash("Invalid current password", "danger")
        return redirect(url_for("dashboard"))

    # Validate new password
    if not new_password or new_password != confirm_password:
        flash("New passwords do not match", "danger")
        return redirect(url_for("dashboard"))

    # Update password in database
    new_password_hash = generate_password_hash(new_password)
    db.execute("UPDATE users SET hash = ? WHERE id = ?", new_password_hash, user_id)

    flash("Password changed successfully!", "success")
    return redirect(url_for("dashboard"))


@app.route("/clargclick/new_username", methods=["POST"])
@login_required
def change_username():
    """Allow users to change their username"""
    user_id = session.get("user_id")
    new_username = request.form.get("username")

    # Validate new username
    if not new_username:
        flash("Username cannot be blank", "danger")
        return redirect(url_for("dashboard"))

    # Check if username is already taken
    existing_user = db.execute("SELECT id FROM users WHERE name = ?", new_username)
    if existing_user and existing_user[0]["id"] != user_id:
        flash("Username already taken", "danger")
        return redirect(url_for("dashboard"))

    # Update username in database
    db.execute("UPDATE users SET name = ? WHERE id = ?", new_username, user_id)

    flash("Username changed successfully!", "success")
    return redirect(url_for("dashboard"))


@app.route("/clargclick/delete_account", methods=["POST"])
@login_required
def delete_account():
    """Allow users to delete their account"""
    user_id = session.get("user_id")

    # Confirmation can be handled in a separate step if needed, e.g., with a modal or separate page.
    # For now, we'll assume the user has confirmed the deletion.

    # Delete user's scores
    db.execute("DELETE FROM scores WHERE user_id = ?", user_id)

    # Delete the user from the database
    db.execute("DELETE FROM users WHERE id = ?", user_id)

    # Log the user out and clear the session
    session.clear()

    flash("Your account has been deleted.", "success")
    return redirect(url_for("index"))


@app.route("/clargclick/new_pfp", methods=["POST"])
@login_required
def new_pfp():
    user_id = session.get("user_id")
    new_pfp = request.files.get("new_pfp")
    if new_pfp:
        new_pfp_data = convertToBinaryData(new_pfp)
        db.execute("UPDATE users SET profile_picture = ? WHERE id = ?", new_pfp_data, user_id)
    else:
        flash("File Error")
    return redirect(url_for("dashboard"))


@app.route("/contact", methods=["GET"])
def contact():
    return render_template("contact.html")


@app.route("/clargclick/secret_clarg", methods=["POST"])
@login_required
def secret_clarg():
    user_id = session.get("user_id")

    if not user_id:
        flash("Please login to collect Clarg", "danger")
        return redirect(url_for("index"))

    try:
        # 1. Fetch the user's current clargs_owned data
        current_clargs_owned = db.execute("SELECT clargs_owned FROM users WHERE id = ?", user_id)[
            0]["clargs_owned"]
        clargs_owned = json.loads(current_clargs_owned)

        # 2. Unlock the secret_clarg
        clargs_owned["secret_clarg"]["unlocked"] = True

        # 3. Update the database with the modified clargs_owned
        db.execute("UPDATE users SET clargs_owned = ? WHERE id = ?",
                   json.dumps(clargs_owned), user_id)

        flash("You've unlocked the Secret Clarg!", "success")

    except Exception as e:
        print(f"Error unlocking secret clarg: {e}")
        flash("An error occurred. Please try again later.", "danger")

    return redirect(url_for("index"))


@app.route("/clargclick/clarg_unlock", methods=["POST"])
@login_required
def clarg_unlock():
    user_id = session.get("user_id")

    if not user_id:
        flash("Please login to unlock Clargs", "danger")
        return redirect(url_for("index"))

    try:
        # Fetch the user's current clargs_owned data
        current_clargs_owned = db.execute("SELECT clargs_owned FROM users WHERE id = ?", user_id)[
            0]["clargs_owned"]
        clargs_owned = json.loads(current_clargs_owned)

        # Determine which clarg to unlock based on the request
        clarg_to_unlock = request.form.get("clarg_type")

        # Check if the clarg_to_unlock is valid and not already unlocked
        if clarg_to_unlock in clargs_owned and not clargs_owned[clarg_to_unlock]["unlocked"]:
            if clarg_to_unlock == "dr_clarg":
                # Correctly determine the user's rank
                clicktotal = db.execute("SELECT clicktotal FROM users WHERE id = ?", user_id)[0]["clicktotal"]
                if clicktotal is not None and clicktotal >= 5000:
                    clargs_owned["dr_clarg"]["unlocked"] = True
                    db.execute("UPDATE users SET clargs_owned = ? WHERE id = ?",
                               json.dumps(clargs_owned), user_id)
                    flash("You've unlocked the Dr Clarg!", "success")
                else:
                    flash("You need to have at least 5,000 clicks total to unlock Dr Clarg", "danger")

            # Check if the user is in the top 2 of the leaderboard
            elif clarg_to_unlock == "ben_clarg":
                # Correctly determine the user's rank # change to clicks
                clicktotal = db.execute("SELECT clicktotal FROM users WHERE id = ?", user_id)[0]["clicktotal"]

                if clicktotal is not None and clicktotal >= 100000:
                    clargs_owned["ben_clarg"]["unlocked"] = True
                    db.execute("UPDATE users SET clargs_owned = ? WHERE id = ?",
                               json.dumps(clargs_owned), user_id)

                current_name = db.execute("SELECT name FROM users WHERE id = ?", user_id)[0]["name"]

                # 4. Append the title if they don't already have it
                suffix = " (Ben Clarg owner btw)"
                if suffix not in current_name:
                    new_name = current_name + suffix
                    db.execute("UPDATE users SET name = ? WHERE id = ?", new_name, user_id)
                    # Update session just in case, though usually not needed if fetching from DB

                    flash("You've unlocked the Ben Sadik Clarg!", "success")
                else:
                    flash("You need to have at least 100,000 clicks total to unlock Ben Sadik Clarg", "danger")

            elif clarg_to_unlock == "buisness_clarg":
                # Correctly determine the user's rank # change to clicks
                clicktotal = db.execute("SELECT clicktotal FROM users WHERE id = ?", user_id)[0]["clicktotal"]

                if clicktotal is not None and clicktotal >= 10000:
                    clargs_owned["business_clarg"]["unlocked"] = True
                    db.execute("UPDATE users SET clargs_owned = ? WHERE id = ?",
                               json.dumps(clargs_owned), user_id)
                    flash("You've unlocked the Business Clarg!", "success")
                else:
                    flash("You need to have at least 10,000 clicks total to unlock Buisness Clarg", "danger")


            elif clarg_to_unlock == "jamaican_clarg":
                # Correctly determine the user's rank # change to clicks
                clicktotal = db.execute("SELECT clicktotal FROM users WHERE id = ?", user_id)[0]["clicktotal"]

                if clicktotal is not None and clicktotal >= 55000:
                    clargs_owned["jamaican_clarg"]["unlocked"] = True
                    db.execute("UPDATE users SET clargs_owned = ? WHERE id = ?",
                               json.dumps(clargs_owned), user_id)
                    flash("You've unlocked the Jamaican Clarg!", "success")
                else:
                    flash("You need to have at least 55,000 clicks total to unlock Jamaican Clarg", "danger")

            elif clarg_to_unlock == "vacation_clarg":
                # Correctly determine the user's clicktotal
                clicktotal = db.execute("SELECT clicktotal FROM users WHERE id = ?", user_id)[0]["clicktotal"]

                if clicktotal is not None and clicktotal >= 30000: # Changed <= to >=
                    clargs_owned["vacation_clarg"]["unlocked"] = True
                    db.execute("UPDATE users SET clargs_owned = ? WHERE id = ?",
                            json.dumps(clargs_owned), user_id)
                    flash("You've unlocked the Vacation Clarg!", "success")
                else:
                    flash("You need to have at least 30,000 clicks total to unlock Vacation Clarg", "danger") #Added at least to the error message

            # Handle other clarg unlock logic (if needed)
            elif clarg_to_unlock:
                clargs_owned[clarg_to_unlock]["unlocked"] = True
                db.execute("UPDATE users SET clargs_owned = ? WHERE id = ?",
                       json.dumps(clargs_owned), user_id)
                flash(f"You've unlocked the {clarg_to_unlock} Clarg!", "success")

        else:
            flash("Invalid Clarg or Clarg already unlocked", "danger")

    except Exception as e:
        print(f"Error unlocking clarg: {e}")
        flash("An error occurred. Please try again later.", "danger")

    return redirect(url_for("dashboard"))

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json() or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"ok": False, "error": "Empty suggestion"}), 400
    today = date.today().isoformat()
    user_id = session.get("user_id")
    if not user_id:
        username = "guest"
    else:
        row = db.execute("SELECT name FROM users WHERE id = ?", user_id)
        username = row[0]["name"]
    formatted_time = datetime.now(est).strftime("%I:%M %p").lstrip("0")
    db.execute("INSERT INTO suggestions (username, text, submitted_date, timestamp) VALUES (?, ?, ?, ?)", username, text, today, formatted_time)
    return jsonify({"ok": True})

@app.route('/ads.txt')
@app.route('/README.md')

@app.route('/appetizers/appetizers.json')
def appetizers():
    # Because this is INSIDE the function, Flask reads the live file on every page load
    file_path = '/home/jaxeuseuse/ClargClick/appetizers/appetizers.json'

    with open(file_path, 'r') as file:
        data = json.load(file)

    return jsonify(data)

@app.route('/robots.txt')
@app.route('/sitemap.xml')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])
@app.route('/')
def indexBASE():
    return render_template("indexBASE.html")
@app.route('/club', methods=["GET", "POST"])
def club():
    return render_template("club.html")
@app.route('/about', methods=["GET", "POST"])
def aboutBASE():
    return render_template("aboutBASE.html")
@app.route('/games', methods=["GET", "POST"])

@app.route('/getsammy', methods=["GET", "POST"])
def indexGET():
    return render_template("indexGET.html")