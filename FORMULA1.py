"""L1=cQ1/f1
L2=cQ2/f2
c=299,792,458
Q1=L5C
Q2=L9C
f1=1176.45 
f2=2492.028"""

c = 299_792_458  # Speed of light in meters per second
f1 = 1176.45  # Frequency f1 in MHz
f2 = 2492.028  # Frequency f2 in MHz

# Convert frequencies from MHz to Hz
f1_hz = f1 * 1e6
f2_hz = f2 * 1e6

# Sample data for L5C (Q1) and LSC (Q2)
L5C_values = [1e-9, 2e-9, 3e-9, 4e-9, 5e-9]  # Example values in seconds
LSC_values = [1e-9, 2.5e-9, 3.5e-9, 4.5e-9, 5.5e-9]  # Example values in seconds

# Calculate L1 and L2
L1_values = [c * Q1 / f1_hz for Q1 in L5C_values]
L2_values = [c * Q2 / f2_hz for Q2 in LSC_values]

# Output the results
print("L5C (Q1) values:", L5C_values)
print("LSC (Q2) values:", LSC_values)
print("Calculated L1 values:", L1_values)
print("Calculated L2 values:", L2_values)
