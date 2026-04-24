import json
from cs50 import SQL

# --- CONFIGURE THIS ---
# 1. Set the path to your database
db = SQL("sqlite:////home/jaxeuseuse/ClargClick/clargclick.db")
# 2. Set the ID of the user you want to fix
user_id_to_fix = 1 # <--- CHANGE THIS TO YOUR USER ID
# --------------------

try:
    # 1. FETCH the current clargs_owned data from the database
    # It will be a JSON string
    rows = db.execute("SELECT clargs_owned FROM users WHERE id = ?", user_id_to_fix)

    if not rows:
        print(f"Error: No user found with ID {user_id_to_fix}")
    else:
        current_clargs_string = rows[0]["clargs_owned"]
        print(f"Original data: {current_clargs_string}")

        # 2. PARSE the JSON string into a Python dictionary
        clargs_owned = json.loads(current_clargs_string)

        # 3. MODIFY the values for 'jamaican_clarg'
        if 'jamaican_clarg' in clargs_owned:
            clargs_owned['jamaican_clarg']['unlocked'] = False
            clargs_owned['jamaican_clarg']['selected'] = False
        else:
            print("Warning: 'jamaican_clarg' not found in data. No changes made.")

        # 4. CONVERT the modified dictionary back into a JSON string
        new_clargs_string = json.dumps(clargs_owned)
        print(f"New data to save: {new_clargs_string}")

        # 5. WRITE the new JSON string back to the database
        db.execute("UPDATE users SET clargs_owned = ? WHERE id = ?", new_clargs_string, user_id_to_fix)

        print("\n✅ Success! The 'jamaican_clarg' values have been reset to false.")

except Exception as e:
    print(f"\n❌ An error occurred: {e}")