import pandas as pd
from datetime import datetime
import re

# Load multiple timetable CSVs with proper column handling
df1 = pd.read_csv("civil_timetable.csv").fillna("")
df2 = pd.read_csv("datascience.csv").fillna("")
df3 = pd.read_csv("eee.csv").fillna("")

# Standardize column names across all dataframes
# Civil has both Block and Classroom columns, let's use Classroom
if 'Classroom' not in df1.columns and 'Block' in df1.columns:
    df1['Classroom'] = df1['Block']

# Data Science has both Block and Classroom columns
if 'Classroom' not in df2.columns and 'Block' in df2.columns:
    df2['Classroom'] = df2['Block']

# Ensure all dataframes have the required columns
required_columns = ['Department', 'Classroom', 'Day', 'Slot', 'Subject', 'Faculty']

for df in [df1, df2, df3]:
    for col in required_columns:
        if col not in df.columns:
            df[col] = ""

# Select only the required columns to ensure consistent structure
df1 = df1[required_columns]
df2 = df2[required_columns]
df3 = df3[required_columns]

# Combine into one DataFrame
df = pd.concat([df1, df2, df3], ignore_index=True)

def clean_time_str(tstr):
    if not isinstance(tstr, str):
        return ""
    tstr = tstr.replace("\n", "").replace(" ", "").replace("S", "").replace("s", "")
    tstr = tstr.replace(".", ":").lower()
    # If already has am/pm, return as is
    if "am" in tstr or "pm" in tstr:
        return tstr
    # Add am/pm if missing and possible
    if re.match(r"^\d{1,2}:\d{2}$", tstr):
        h, m = map(int, tstr.split(":"))
        if h < 8:
            tstr += "pm"
        else:
            tstr += "am"
    return tstr

def parse_time(tstr):
    tstr = clean_time_str(tstr)
    # Try with am/pm
    for fmt in ("%I:%M%p", "%H:%M"):
        try:
            return datetime.strptime(tstr, fmt).time()
        except:
            continue
    # Try without am/pm
    try:
        h, m = map(int, tstr.split(":"))
        return datetime.strptime(f"{h}:{m}", "%H:%M").time()
    except:
        return None

def get_csv_slot_range(slot_str):
    try:
        slot_str = str(slot_str).replace("\n", "").replace(" ", "")
        
        # Handle different slot formats
        if ":" in slot_str and "-" in slot_str:
            # Standard format like "8:50-9:40" or "S8.50am-9.40am"
            parts = slot_str.split("-")
            
            # Clean up the parts
            start_part = parts[0].replace("S", "").replace("s", "")
            end_part = parts[1]
            
            start = parse_time(start_part)
            end = parse_time(end_part)
            
            return start, end
        else:
            return None, None
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
        slot_str = str(row["Slot"])
        
        # Skip empty slots or free periods
        if not slot_str or slot_str.lower() in ["free", "break", ""]:
            continue
            
        start, end = get_csv_slot_range(slot_str)
        
        if start and end and start <= qtime <= end:
            results.append((row, start, end))
    
    return results

def check_all_classrooms(day, query_time_str):
    """List all classrooms with a slot covering the given time, and show if occupied or free."""
    qtime = parse_query_time(query_time_str)
    if not qtime:
        return f"Invalid time input: {query_time_str}"

    output_lines = [f"At {query_time_str} on {day}:"]
    # For each row, check if the slot covers the time
    day_rows = df[df["Day"].str.lower() == day.lower()]
    found_any = False
    for _, row in day_rows.iterrows():
        slot_str = str(row["Slot"])
        if slot_str and "-" in slot_str:
            start, end = get_csv_slot_range(slot_str)
            if start and end and start <= qtime <= end:
                dept = row["Department"]
                classroom = row["Classroom"]
                subject = str(row["Subject"]).strip()
                faculty = str(row.get("Faculty", "")).strip()
                start_str = start.strftime("%H:%M") if start else "N/A"
                end_str = end.strftime("%H:%M") if end else "N/A"
                if subject == "" or subject.lower() in ["free", "break"]:
                    status = "FREE"
                else:
                    status = f"OCCUPIED ({subject}{', '+faculty if faculty else ''})"
                output_lines.append(f"- {dept} {classroom} [{start_str}-{end_str}] → {status}")
                found_any = True
    if not found_any:
        output_lines.append("No classes found at this time.")
    return "\n".join(output_lines)

# Example usage:
day_input = input("Enter the day (e.g., Wednesday): ")
time_input = input("Enter the time (e.g., 14:00): ")
print(check_all_classrooms(day_input, time_input))