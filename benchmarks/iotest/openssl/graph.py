import pandas as pd
import matplotlib.pyplot as plt

# Load your results
df = pd.read_csv('benchmark_results.csv')

# Calculate the mean throughput for each size
stats = df.groupby('Size')['Throughput_MBs'].mean().reindex(['1KB', '64KB', '256KB', '1MB', '16MB'])

# Plotting
plt.figure(figsize=(10, 6))
stats.plot(kind='line', marker='o', linewidth=2, color='#2c3e50')

plt.title('I/O Backend Throughput Scalability (2025)', fontsize=14)
plt.xlabel('Buffer / File Size', fontsize=12)
plt.ylabel('Throughput (MB/s)', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.7)
plt.xscale('category') # Or use log scale if using numeric bytes

plt.savefig('throughput_benchmark.png')
plt.show()

