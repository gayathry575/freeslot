import pandas as pd
from datetime import datetime

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
    tstr = tstr.replace("\n", "").replace(" ", "").lower()
    tstr = tstr.replace("s", "").replace(".", ":")
    # Handle special cases for civil timetable
    if "pm" in tstr and "am" in tstr:
        # Handle cases like "10:45am-11:35pm" which should be "10:45am-11:35am"
        parts = tstr.split("-")
        if len(parts) == 2:
            if parts[0].endswith("am") and parts[1].endswith("pm"):
                # Check if the second time should actually be am
                time_part = parts[1].replace("pm", "")
                try:
                    h, m = time_part.split(":")
                    if int(h) < 12:  # If hour is less than 12, it should be am
                        parts[1] = parts[1].replace("pm", "am")
                        tstr = "-".join(parts)
                except:
                    pass
    return tstr

def parse_time(tstr):
    tstr = clean_time_str(tstr)
    
    # Handle special case for "10:45am-11:35pm" which should be "10:45am-11:35am"
    if "pm" in tstr and "am" in tstr:
        parts = tstr.split("-")
        if len(parts) == 2:
            if parts[0].endswith("am") and parts[1].endswith("pm"):
                time_part = parts[1].replace("pm", "")
                try:
                    h, m = time_part.split(":")
                    if int(h) < 12:  # If hour is less than 12, it should be am
                        tstr = parts[0] + "-" + parts[1].replace("pm", "am")
                except:
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
        
        if subject == "" or subject.lower() in ["free", "break"]:
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
            (df["Classroom"] == classroom) &
            (df["Day"].str.lower() == day.lower())
        ]
        
        if not row_match.empty:
            # Find the row that matches our time
            found = False
            for _, row in row_match.iterrows():
                slot_str = str(row["Slot"])
                if slot_str and "-" in slot_str:
                    start, end = get_csv_slot_range(slot_str)
                    if start and end and start <= qtime <= end:
                        start_str = start.strftime("%H:%M") if start else "N/A"
                        end_str = end.strftime("%H:%M") if end else "N/A"
                        line = f"- {dept} {classroom} [{start_str}-{end_str}] → {status}"
                        output_lines.append(line)
                        found = True
                        break
            if not found:
                line = f"- {dept} {classroom} → {status}"
                output_lines.append(line)
        else:
            line = f"- {dept} {classroom} → {status}"
            output_lines.append(line)
    
    return "\n".join(output_lines)

# Example usage:
day_input = input("Enter the day (e.g., Wednesday): ")
time_input = input("Enter the time (e.g., 14:00): ")
print(check_all_classrooms(day_input, time_input))