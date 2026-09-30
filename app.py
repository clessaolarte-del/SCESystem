from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.config["SECRET_KEY"] = "sersystem-secret-key"
app.config["DATABASE"] = os.path.join(os.path.dirname(__file__), "data", "sersystem.db")

os.makedirs(os.path.dirname(app.config["DATABASE"]), exist_ok=True)


def get_db():
    conn = sqlite3.connect(app.config["DATABASE"])
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            user_type TEXT NOT NULL CHECK(user_type IN ('student', 'staff'))
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            location TEXT NOT NULL,
            condition TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,
            available_quantity INTEGER NOT NULL DEFAULT 0,
            image_url TEXT,
            description TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            purpose TEXT NOT NULL,
            location TEXT NOT NULL,
            borrowed_at TEXT NOT NULL,
            due_at TEXT,
            returned_at TEXT,
            status TEXT NOT NULL DEFAULT 'borrowed',
            remarks TEXT,
            FOREIGN KEY (equipment_id) REFERENCES equipment (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    if conn.execute("SELECT COUNT(*) FROM equipment").fetchone()[0] == 0:
        sample_equipment = [
            ("Laptop (Dell)", "Laptop", "IT Office", "Good", 5, 5,
             "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=500&h=400&q=80",
             "Dell laptop for academic and project use."),
            ("Projector", "Projector", "AV Room", "Good", 3, 3,
             "https://images.unsplash.com/photo-1516321165247-4aa89a48be28?auto=format&fit=crop&w=500&h=400&q=80",
             "Projector for classroom presentations."),
            ("Camera (Canon)", "Camera", "IT Office", "Good", 4, 4,
             "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=500&h=400&q=80",
             "Canon camera for media assignments."),
            ("Tripod", "Accessories", "IT Office", "Good", 6, 6,
             "https://images.unsplash.com/photo-1610827033614-f20a73aee18c?auto=format&fit=crop&w=500&h=400&q=80",
             "Adjustable tripod for camera support."),
            ("Microphone", "Audio", "Audio Room", "Good", 5, 5,
             "https://images.unsplash.com/photo-1511379938547-c1f69419868d?auto=format&fit=crop&w=500&h=400&q=80",
             "Portable microphone for presentations."),
            ("Speaker", "Audio", "Audio Room", "Good", 4, 4,
             "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=500&h=400&q=80",
             "High-quality classroom speaker."),
            ("Tablet", "Tablet", "Library", "Good", 4, 4,
             "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=500&h=400&q=80",
             "Tablet for class notes and research."),
            ("Whiteboard", "Office", "Classroom 1", "Good", 2, 2,
             "https://images.unsplash.com/photo-1552664730-d307ca884978?auto=format&fit=crop&w=500&h=400&q=80",
             "Portable whiteboard for team activities.")
        ]
        conn.executemany(
            "INSERT INTO equipment (name, category, location, condition, quantity, available_quantity, image_url, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            sample_equipment,
        )

    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        conn.execute(
            "INSERT INTO users (name, email, password_hash, user_type) VALUES (?, ?, ?, ?)",
            ("Juan Dela Cruz", "student@example.com", generate_password_hash("student123"), "student"),
        )
        conn.execute(
            "INSERT INTO users (name, email, password_hash, user_type) VALUES (?, ?, ?, ?)",
            ("Admin User", "admin@example.com", generate_password_hash("admin123"), "staff"),
        )

    conn.commit()
    conn.close()


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


@app.context_processor
def inject_current_user():
    return {"current_user": current_user()}


@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter your email and password.", "error")
            return render_template("login.html")

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_type"] = user["user_type"]
            session["name"] = user["name"]
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        user_type = request.form.get("user_type", "student")

        if not name or not email or not password:
            flash("Please complete all fields.", "error")
            return render_template("register.html")

        conn = get_db()
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            flash("An account with this email already exists.", "error")
            conn.close()
            return render_template("register.html")

        conn.execute(
            "INSERT INTO users (name, email, password_hash, user_type) VALUES (?, ?, ?, ?)",
            (name, email, generate_password_hash(password), user_type),
        )
        conn.commit()
        conn.close()

        flash("Account created successfully. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    conn = get_db()

    recent_transactions = conn.execute(
        """
        SELECT t.*, e.name AS equipment_name
        FROM transactions t
        JOIN equipment e ON e.id = t.equipment_id
        WHERE t.user_id = ?
        ORDER BY t.id DESC
        LIMIT 5
        """,
        (user["id"],),
    ).fetchall()

    equipment = conn.execute("SELECT * FROM equipment ORDER BY id ASC LIMIT 8").fetchall()

    if user["user_type"] == "student":
        borrowed_count = conn.execute("SELECT COUNT(*) FROM transactions WHERE user_id = ? AND status = 'borrowed'", (user["id"],)).fetchone()[0]
        returned_count = conn.execute("SELECT COUNT(*) FROM transactions WHERE user_id = ? AND status = 'returned'", (user["id"],)).fetchone()[0]
    else:
        borrowed_count = conn.execute("SELECT COUNT(*) FROM transactions WHERE status = 'borrowed'").fetchone()[0]
        returned_count = conn.execute("SELECT COUNT(*) FROM transactions WHERE status = 'returned'").fetchone()[0]

    metrics = {
        "total_equipment": conn.execute("SELECT COUNT(*) FROM equipment").fetchone()[0],
        "available": conn.execute("SELECT SUM(available_quantity) FROM equipment").fetchone()[0] or 0,
        "borrowed": borrowed_count,
        "returned": returned_count,
    }

    conn.close()
    return render_template("dashboard.html", metrics=metrics, equipment=equipment, recent_transactions=recent_transactions, page_title="Dashboard")


@app.route("/equipment", methods=["GET", "POST"])
@login_required
def equipment():
    user = current_user()
    conn = get_db()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "borrow":
            if user["user_type"] != "student":
                flash("Only students can borrow equipment.", "error")
                return redirect(url_for("equipment"))

            equipment_id = int(request.form.get("equipment_id"))
            purpose = request.form.get("purpose", "Research Project")
            location = request.form.get("location", "IT Office")
            due_at = request.form.get("due_at") or (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M")

            item = conn.execute("SELECT * FROM equipment WHERE id = ?", (equipment_id,)).fetchone()
            if not item:
                flash("Equipment not found.", "error")
                return redirect(url_for("equipment"))
            if item["available_quantity"] <= 0:
                flash("This equipment is currently unavailable.", "error")
                return redirect(url_for("equipment"))

            conn.execute(
                "INSERT INTO transactions (equipment_id, user_id, purpose, location, borrowed_at, due_at, status) VALUES (?, ?, ?, ?, ?, ?, 'borrowed')",
                (equipment_id, user["id"], purpose, location, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), due_at),
            )
            conn.execute(
                "UPDATE equipment SET available_quantity = available_quantity - 1 WHERE id = ?",
                (equipment_id,),
            )
            conn.commit()
            flash(f"{item['name']} borrowed successfully.", "success")
            return redirect(url_for("equipment"))

        if action == "return":
            transaction_id = int(request.form.get("transaction_id"))
            equipment_id = int(request.form.get("equipment_id"))
            conn.execute(
                "UPDATE transactions SET returned_at = ?, status = 'returned' WHERE id = ? AND user_id = ?",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), transaction_id, user["id"]),
            )
            conn.execute(
                "UPDATE equipment SET available_quantity = available_quantity + 1 WHERE id = ?",
                (equipment_id,),
            )
            conn.commit()
            flash("Equipment returned successfully.", "success")
            return redirect(url_for("equipment"))

    equipment_list = conn.execute("SELECT * FROM equipment ORDER BY category, name").fetchall()

    if user["user_type"] == "student":
        my_borrowings = conn.execute(
            """
            SELECT t.*, e.name AS equipment_name
            FROM transactions t
            JOIN equipment e ON e.id = t.equipment_id
            WHERE t.user_id = ?
            ORDER BY t.id DESC
            """,
            (user["id"],),
        ).fetchall()
    else:
        my_borrowings = conn.execute(
            """
            SELECT t.*, e.name AS equipment_name, u.name AS user_name
            FROM transactions t
            JOIN equipment e ON e.id = t.equipment_id
            JOIN users u ON u.id = t.user_id
            ORDER BY t.id DESC
            LIMIT 20
            """
        ).fetchall()

    conn.close()
    return render_template("equipment.html", equipment=equipment_list, my_borrowings=my_borrowings, page_title="Equipment")


@app.route("/reports")
@login_required
def reports():
    user = current_user()
    if user["user_type"] != "staff":
        flash("Access restricted to staff only.", "error")
        return redirect(url_for("dashboard"))

    conn = get_db()
    transactions = conn.execute(
        """
        SELECT t.*, e.name AS equipment_name, u.name AS user_name
        FROM transactions t
        JOIN equipment e ON e.id = t.equipment_id
        JOIN users u ON u.id = t.user_id
        ORDER BY t.id DESC
        """
    ).fetchall()
    conn.close()

    return render_template("reports.html", transactions=transactions, page_title="Reports")


init_db()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
