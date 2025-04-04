import csv
import datetime
import os
from datetime import datetime as dt

def parse_date_range(date_str):
    """Parse a date or date range string into individual dates."""
    dates = []
    
    # Remove any leading/trailing whitespace
    date_str = date_str.strip()
    
    months = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, 
             "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
    
    # Check if it's an ongoing event
    if "ongoing" in date_str.lower():
        # Extract the start date if available (e.g., "Jan 2, 2024 - ongoing")
        if "-" in date_str:
            start_date_str = date_str.split("-")[0].strip()
            try:
                # Parse start date
                start_parts = start_date_str.split()
                start_month = months.get(start_parts[0], 1)
                start_day = int(start_parts[1].replace(",", ""))
                start_year = int(start_parts[2])
                
                # Create start date
                start_date = dt(start_year, start_month, start_day)
                
                # Add only the first two dates
                dates.append(start_date)
                dates.append(start_date + datetime.timedelta(days=1))
            except Exception as e:
                print(f"Error parsing ongoing date '{date_str}': {e}")
                # Use today and tomorrow as fallback
                today = dt.today()
                dates.append(today)
                dates.append(today + datetime.timedelta(days=1))
        else:
            # No start date available, use today and tomorrow
            today = dt.today()
            dates.append(today)
            dates.append(today + datetime.timedelta(days=1))
        
        return dates
    
    elif "-" in date_str:
        # Handle date range
        parts = date_str.split("-")
        start_date_str = parts[0].strip()
        end_date_str = parts[1].strip()
        
        try:
            # If start date doesn't have month/year info, borrow from end date
            if len(start_date_str.split()) == 1:
                month_year = " ".join(end_date_str.split()[1:])
                start_date_str = f"{start_date_str} {month_year}"
            
            # Parse start date
            start_parts = start_date_str.split()
            start_month = months.get(start_parts[0], 1)
            start_day = int(start_parts[1].replace(",", ""))
            start_year = int(start_parts[-1]) if len(start_parts) > 2 else int(end_date_str.split()[-1])
            
            # Parse end date
            end_parts = end_date_str.split()
            end_month = months.get(end_parts[0], start_month) if len(end_parts) > 1 else start_month
            end_day = int(end_parts[1].replace(",", "")) if len(end_parts) > 1 else int(end_parts[0].replace(",", ""))
            end_year = int(end_parts[-1]) if len(end_parts) > 2 else start_year
            
            # Create datetime objects
            start_date = dt(start_year, start_month, start_day)
            end_date = dt(end_year, end_month, end_day)
            
            # Generate all dates in the range
            current_date = start_date
            while current_date <= end_date:
                dates.append(current_date)
                current_date += datetime.timedelta(days=1)
        except Exception as e:
            print(f"Error parsing date range '{date_str}': {e}")
            # Add a default date when parsing fails
            today = dt.today()
            dates.append(today)
    else:
        # Parse single date
        try:
            parts = date_str.split()
            if len(parts) >= 3:
                month = months.get(parts[0], 1)
                day = int(parts[1].replace(",", ""))
                year = int(parts[2])
                
                dates.append(dt(year, month, day))
            else:
                print(f"Could not parse date '{date_str}', using today's date")
                dates.append(dt.today())
        except Exception as e:
            print(f"Error parsing date '{date_str}': {e}")
            # Add a default date when parsing fails
            dates.append(dt.today())
    
    return dates

def format_date(date):
    """Format the date as M/D/YYYY."""
    return f"{date.month}/{date.day}/{date.year}"

# Set file paths relative to the script's location
input_file = "datasets/calendar_unparsedevents.csv"
output_file = "datasets/calendar_parsedevents.csv"

# Print CSV contents for debugging
print("CSV Contents:")
try:
    with open(input_file, 'r') as f:
        for i, line in enumerate(f):
            print(f"Line {i}: {line.strip()}")
except Exception as e:
    print(f"Error reading file: {e}")

# Process the CSV
try:
    with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        
        # Write header
        header = next(reader)
        writer.writerow(header)
        
        # Process each row
        for row in reader:
            title = row[0]
            dates_str = row[1]
            
            # Parse the dates
            dates = parse_date_range(dates_str)
            
            # Write a row for each date
            for date in dates:
                formatted_date = format_date(date)
                writer.writerow([title, formatted_date])
    
    print(f"Expanded dates have been written to {output_file}")
except Exception as e:
    print(f"An error occurred: {e}")