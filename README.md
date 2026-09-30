# Student Equipment and Returning Management System

A Python Flask application inspired by the provided design mockup for a school equipment lending system.

## Features

- Student login and account creation
- Staff/faculty dashboard and reports
- View available equipment and borrow items
- Return borrowed equipment
- Responsive UI similar to the provided system mockup
- Flowchart page describing the process
- SQLite database with sample data

## Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
   On macOS/Linux:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:
   ```bash
   python app.py
   ```

4. Open in browser:
   ```text
   http://localhost:5000
   ```

## Default accounts

- Student: `student@example.com` / `student123`
- Staff: `admin@example.com` / `admin123`

## Project structure

- `app.py` — Flask app and database setup
- `templates/` — HTML pages
- `static/css/style.css` — styling
- `data/` — SQLite database

## Notes

This is a working prototype that focuses on the system flow and interface design. You can extend it with admin management, inventory editing, and authentication improvements.
