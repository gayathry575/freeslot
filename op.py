from flask import Flask, render_template, request
import pandas as pd
import re

app = Flask(__name__)

# -------------------------
# Helper Functions
# -------------------------
def load_timetable_data(files):
    all_data = []
    for file in files:
        df = pd.read_csv(file)
        all_data.append(df)
    return pd.concat(all_data, ignore_index=True)

def parse_time_input(time_str):
    try:
        if ':' in time_str:
            hours, minutes = map(int, time_str.split(':'))
        else:
            hours = int(time_str)
            minutes = 0
        return hours * 60 + minutes
    except:
        return None

def parse_slot_time(slot_str):
    match = re.search(r'S?(\d+\.\d+)(am|pm)?\s*-\s*(\d+\.\d+)(am|pm)?', str(slot_str), re.IGNORECASE)
    if not match:
        return None, None
    
    start_time_str, start_period, end_time_str, end_period = match.groups()

    def convert_to_minutes(time_str, period):
        time_str = time_str.replace('.', ':')
        if ':' in time_str:
            hours, minutes = map(int, time_str.split(':'))
        else:
            hours = int(time_str)
            minutes = 0

        # Convert to 24-hour format
        if period and period.lower() == 'pm' and hours != 12:
            hours += 12
        elif period and period.lower() == 'am' and hours == 12:
            hours = 0
        return hours * 60 + minutes

    start_minutes = convert_to_minutes(start_time_str, start_period)
    end_minutes = convert_to_minutes(end_time_str, end_period)
    return start_minutes, end_minutes

def find_free_classrooms(day, time_str, df):
    time_minutes = parse_time_input(time_str)
    if time_minutes is None:
        return "Invalid time format. Please use HH:MM format.", None

    # ✅ NEW CONDITION: Before 08:00 or after 16:35 → College Over
    if time_minutes < (8 * 60) or time_minutes > (16 * 60 + 35):
        return "College Over – No Classes", None

    day_data = df[df['Day'].str.lower() == day.lower()]
    if day_data.empty:
        return f"No data available for {day}.", None

    free_classrooms = []
    occupied_classrooms = []

    for _, row in day_data.iterrows():
        start_minutes, end_minutes = parse_slot_time(row['Slot'])
        if start_minutes is None or end_minutes is None:
            continue

        if start_minutes <= time_minutes < end_minutes:
            subject = str(row['Subject'])
            if (pd.isna(subject) or subject.strip() == '' or subject.lower() in ['nan', 'break', 'mentor hour']):
                free_classrooms.append({
                    'Department': row['Department'],
                    'Block': row['Block'],
                    'Classroom': row['Classroom'],
                    'Slot': row['Slot']
                })
            else:
                occupied_classrooms.append({
                    'Department': row['Department'],
                    'Block': row['Block'],
                    'Classroom': row['Classroom'],
                    'Subject': subject,
                    'Slot': row['Slot']
                })
    return free_classrooms, occupied_classrooms

# -------------------------
# Routes
# -------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    csv_files = ['datascience.csv','civil.csv']
    df = load_timetable_data(csv_files)

    results = None
    error = None

    if request.method == "POST":
        day = request.form.get("day")
        time_str = request.form.get("time")

        free_classrooms, occupied_classrooms = find_free_classrooms(day, time_str, df)

        if isinstance(free_classrooms, str):  # error or college over case
            error = free_classrooms
        else:
            results = {
                "day": day,
                "time": time_str,
                "free": free_classrooms,
                "occupied": occupied_classrooms
            }

    return render_template("index.html", results=results, error=error)

if __name__ == "__main__":
    app.run(debug=True)
