import pandas as pd
from datetime import datetime
# Load multiple timetable CSVs
df1 = pd.read_csv("civil_timetable.csv").fillna("")
df2 = pd.read_csv("datascience.csv").fillna("")
# Combine into one DataFrame
df = pd.concat([df1, df2], ignore_index=True)
def clean_time_str(tstr):
    if not isinstance(tstr, str):
        return ""
    tstr = tstr.replace("\n", "").replace(" ", "").lower()
    tstr = tstr.replace("s", "").replace(".", ":")
    return tstr
def parse_time(tstr):
    tstr = clean_time_str(tstr)
    if tstr.endswith("pm") and len(tstr) <= 4:
        # e.g., '2:00pm' or '12:30pm'
        pass
    # Fix for wrong 'pm' in morning hours if needed
    if tstr.endswith("pm"):
        try:
            test = datetime.strptime(tstr, "%I:%M%p")
            if test.hour < 8:  # assume am if hour <8 but marked pm
                tstr = tstr.replace("pm", "am")
        except:
            pass
    try:
        return datetime.strptime(tstr, "%I:%M%p").time()
    except:
        try:
            return datetime.strptime(tstr, "%H:%M").time()
        except:
            return None
def get_csv_slot_range(slot_str):
    try:
        slot_str = str(slot_str).replace("\n", "").replace(" ", "")
        parts = slot_str.split("-")
        start = parse_time(parts[0])
        end = parse_time(parts[1])
        return start, end
    except:
        return None, None
def parse_query_time(query_time_str):
    query_time_str = query_time_str.strip().lower()
    for fmt in ["%I:%M%p", "%H:%M"]:
        try:
            return datetime.strptime(query_time_str, fmt).time()
        except:
            continue
    # If just hour:minute like '14:00'
    try:
        h, m = query_time_str.split(":")
        h, m = int(h), int(m)
        if 1 <= h <= 6:
            h += 12
        return datetime.strptime(f"{h}:{m}", "%H:%M").time()
    except:
        return None
def get_slots_for_time(day, query_time_str):
    qtime = parse_query_time(query_time_str)
    if not qtime:
        return []
    day_lower = day.lower()
    day_subset = df[df["Day"].str.lower() == day_lower]
    results = []
    for idx, row in day_subset.iterrows():
        start, end = get_csv_slot_range(row["Slot"])
        if start and end and start <= qtime <= end:
            results.append((row, start, end))
    return results
def check_all_classrooms(day, query_time_str):
    """Check all classrooms for occupation status at a given time and day."""
    qtime = parse_query_time(query_time_str)
    if not qtime:
        return f"Invalid time input: {query_time_str}"
    # Get all relevant slots
    matches = get_slots_for_time(day, query_time_str)
    # Collect all classrooms
    classrooms = {}
    for _, row in df.iterrows():
        classroom_id = (row["Department"], row["Classroom"])
        classrooms[classroom_id] = {
            "Department": row["Department"],
            "Classroom": row["Classroom"]
        }
    # Initialize status as free
    status_map = {key: "FREE" for key in classrooms}
    # Mark occupied slots
    for row, start, end in matches:
        dept = row["Department"]
        classroom = row["Classroom"]
        subject = str(row["Subject"]).strip()
        faculty = str(row.get("Faculty", "")).strip()
        key = (dept, classroom)
        if subject == "" or subject.lower() == "break":
            status_map[key] = "FREE"
        else:
            # Mark as occupied
            status_map[key] = f"OCCUPIED ({subject}{', '+faculty if faculty else ''})"
    # Generate output
    output_lines = [f"At {query_time_str} on {day}:"]
    for (dept, classroom), status in status_map.items():
        # Get the relevant slot times for display
        row_match = df[
            (df["Department"] == dept) &
            (df["Classroom"] == classroom)
        ]
        if not row_match.empty:
            row = row_match.iloc[0]
            start, end = get_csv_slot_range(row["Slot"])
            start_str = start.strftime("%H:%M:%S") if start else "N/A"
            end_str = end.strftime("%H:%M:%S") if end else "N/A"
            line = f"- {dept} {classroom} [{start_str}-{end_str}] → {status}"
            output_lines.append(line)
    return "\n".join(output_lines)
# Example usage:
day_input = input("Enter the day (e.g., Wednesday): ")
time_input = input("Enter the time (e.g., 14:00): ")
print(check_all_classrooms(day_input, time_input))

