import pandas as pd
import re

def load_timetable_data(files):
    """Load all timetable CSV files into a single DataFrame"""
    all_data = []
    for file in files:
        df = pd.read_csv(file)
        all_data.append(df)
    
    return pd.concat(all_data, ignore_index=True)

def parse_time_input(time_str):
    """Convert time input like '8:00' to minutes since midnight"""
    try:
        # Handle both HH:MM and H:MM formats
        if ':' in time_str:
            hours, minutes = map(int, time_str.split(':'))
        else:
            # If no colon, assume it's just hours
            hours = int(time_str)
            minutes = 0
        
        return hours * 60 + minutes
    except:
        return None

def parse_slot_time(slot_str):
    """Convert slot string like 'S2.05pm - 2.55pm' to time range in minutes"""
    # Extract the time part from the slot string
    match = re.search(r'S?(\d+\.\d+)(am|pm)?\s*-\s*(\d+\.\d+)(am|pm)?', slot_str, re.IGNORECASE)
    if not match:
        return None, None
    
    start_time_str, start_period, end_time_str, end_period = match.groups()
    
    # Convert to 24-hour format
    def convert_to_minutes(time_str, period):
        # Replace dot with colon for time parsing
        time_str = time_str.replace('.', ':')
        
        # Handle cases where time might be like "2.05" or "2:05"
        if ':' in time_str:
            hours, minutes = map(int, time_str.split(':'))
        else:
            # If no colon, assume it's just hours
            hours = int(time_str)
            minutes = 0
        
        # FIX FOR DATA ERROR: Morning class times should not be PM
        # If period is PM but time is between 1-11, assume it's a data entry error and change to AM
        if period and period.lower() == 'pm' and 1 <= hours <= 11:
            period = 'am'
        
        # Convert to 24-hour format based on period
        if period and period.lower() == 'pm' and hours != 12:
            hours += 12
        elif period and period.lower() == 'am' and hours == 12:
            hours = 0
            
        return hours * 60 + minutes
    
    start_minutes = convert_to_minutes(start_time_str, start_period)
    end_minutes = convert_to_minutes(end_time_str, end_period)
    
    return start_minutes, end_minutes

def find_free_classrooms(day, time_str, df):
    """Find free classrooms for a given day and time"""
    time_minutes = parse_time_input(time_str)
    if time_minutes is None:
        return "Invalid time format. Please use HH:MM format.", None
    
    # Filter for the requested day
    day_data = df[df['Day'].str.lower() == day.lower()]
    if day_data.empty:
        return f"No data available for {day}.", None
    
    free_classrooms = []
    occupied_classrooms = []
    
    # print(f"\nDebug: Looking for time {time_minutes//60}:{time_minutes%60:02d} on {day}")
    
    # Check each classroom for the given time
    for _, row in day_data.iterrows():
        start_minutes, end_minutes = parse_slot_time(row['Slot'])
        
        if start_minutes is None or end_minutes is None:
            # print(f"  Could not parse slot: {row['Slot']}")
            continue
            
        # Debug print to see what's being processed
        # print(f"  Checking {row['Department']} {row['Block']} {row['Classroom']}: {row['Slot']} -> {start_minutes//60}:{start_minutes%60:02d}-{end_minutes//60}:{end_minutes%60:02d}")
        
        # Check if the requested time falls within this slot
        if start_minutes <= time_minutes < end_minutes:
            subject = str(row['Subject'])
            # print(f"    MATCH! Subject: {subject}")
            
            # Classroom is free if subject is empty, NaN, or Break
            if (pd.isna(subject) or subject.strip() == '' or subject == 'nan' or 
                subject.lower() == 'break' or subject.lower() == 'mentor hour'):
                free_classrooms.append({
                    'Department': row['Department'],
                    'Block': row['Block'],
                    'Classroom': row['Classroom'],
                    'Slot': row['Slot']
                })
                # print(f"    FREE: {row['Department']} {row['Block']} {row['Classroom']}")
            else:
                occupied_classrooms.append({
                    'Department': row['Department'],
                    'Block': row['Block'],
                    'Classroom': row['Classroom'],
                    'Subject': subject,
                    'Slot': row['Slot']
                })
                # print(f"    OCCUPIED: {row['Department']} {row['Block']} {row['Classroom']}: {subject}")
        # else:
        #     print(f"    No match (input: {time_minutes//60}:{time_minutes%60:02d})")
    
    return free_classrooms, occupied_classrooms

def main():
    # List of CSV files to process
    csv_files = ['civil_timetable_neat.csv', 'datascience.csv', 'eee.csv']
    
    try:
        # Load all timetable data
        df = load_timetable_data(csv_files)
        print("Timetable data loaded successfully!")
    except Exception as e:
        print(f"Error loading data: {e}")
        return
    
    # Get user input
    day = input("Enter the day (e.g., Monday, Tuesday): ").strip()
    time_str = input("Enter the time in normal way 8:00, 2:45 like that").strip()
    
    # Find free classrooms
    free_classrooms, occupied_classrooms = find_free_classrooms(day, time_str, df)
    
    if isinstance(free_classrooms, str):  # Error message
        print(free_classrooms)
        return
    
    # Display results
    print(f"\nResults for {day} at {time_str}:")
    
    if free_classrooms:
        print("\nFree Classrooms:")
        for room in free_classrooms:
            print(f"{room['Department']} - {room['Block']} - {room['Classroom']} ({room['Slot']})")
    else:
        print("\nNo free classrooms found.")
    
    if occupied_classrooms:
        print("\nOccupied Classrooms:")
        for room in occupied_classrooms:
            print(f"{room['Department']} - {room['Block']} - {room['Classroom']}: {room['Subject']} ({room['Slot']})")

if __name__ == "__main__":
    main()