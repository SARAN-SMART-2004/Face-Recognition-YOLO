import pandas as pd
import random
from datetime import datetime, timedelta
import os

# Create a folder to save the files
folder_path = "/mnt/data/attendance_excels"
os.makedirs(folder_path, exist_ok=True)

# Generate 10 random names (Unknown1 to Unknown10)
names = [f"Unknown{i}" for i in range(1, 11)]

# Generate 10 Excel files for the past 10 days
for i in range(10):
    date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
    filename = f"{date}.xlsx"
    file_path = os.path.join(folder_path, filename)
    
    # Generate random times for each name
    data = {
        "Time": [datetime.now().replace(hour=random.randint(8, 17),
                                        minute=random.randint(0, 59),
                                        second=random.randint(0, 59)).strftime("%H:%M:%S")
                 for _ in names],
        "Name": names
    }
    
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False)

folder_path
