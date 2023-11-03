# filename: print_columns.py

import pandas as pd

# Download and read the CSV file
url = "https://raw.githubusercontent.com/uwdata/draco/master/data/cars.csv"
data = pd.read_csv(url)

# Print the fields in the dataset
print(data.columns)