# filename: download_and_plot.py

import pandas as pd
import matplotlib.pyplot as plt

# Download and read the CSV file
url = "https://raw.githubusercontent.com/uwdata/draco/master/data/cars.csv"
data = pd.read_csv(url)

# Print the fields in the dataset
print(data.columns)

# Plot the relationship between weight and horsepower
plt.scatter(data['Weight'], data['Horsepower(HP)'])

# Label the axes
plt.xlabel('Weight')
plt.ylabel('Horsepower(HP)')

# Add a title to the plot
plt.title('Relationship between Weight and Horsepower')

# Save the plot to a file
plt.savefig('weight_vs_horsepower.png')