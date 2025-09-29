import json
import matplotlib.pyplot as plt

# Replace 'your_file.json' with the actual path to your JSON file
json_file_path = 'results/run_two_qubit_circuit_d79575bc-6371-48a9-a47e-bc3577d618ac.json'

# Load the JSON file
with open(json_file_path, 'r') as f:
    data = json.load(f)

# Access the lists (arrays) from the dictionary
tData = data.get('tData', [])
sigData = data.get('sigData', [])
errData = data.get('errData', [])

t = list(range(len(sigData)))
pattern_length = 14  # 4 + 10
colors = ['#f0f8ff', '#ffe4e1']  # alternating light colors

# Plot the values
plt.figure(figsize=(12, 4))
plt.plot(t, sigData, marker='o', label='Data')

# Highlight regions
for i in range(0, len(sigData), pattern_length):
    color = colors[1]
    plt.axvspan(i, i + 4, color=color, alpha=0.1, label='Calibration' if i == 0 else "")
    plt.axvspan(i + 4, i + pattern_length, color=color, alpha=0.7, label='Measurement' if i == 0 else "")

# Labels and legend
plt.xlabel('Index')
plt.ylabel('Signal data')
plt.legend()
plt.tight_layout()
plt.grid(True)
plt.show()