import pandas as pd
from tkinter import Tk
from tkinter.filedialog import askopenfilename


def parse_nav_header(lines):
    header_data = {}
    for line in lines:
        if "RINEX VERSION / TYPE" in line:
            header_data["version"] = line[:20].strip()
            header_data["file_type"] = line[20:40].strip()
            header_data["satellite_system"] = line[40:60].strip()
        elif "PGM / RUN BY / DATE" in line:
            header_data["program"] = line[:20].strip()
            header_data["run_by"] = line[20:40].strip()
            header_data["date"] = line[40:60].strip()
        elif "IONOSPHERIC CORR" in line:
            iono_type = line[:4].strip()
            iono_values = line[5:].strip().split()
            if "ionospheric_corrections" not in header_data:
                header_data["ionospheric_corrections"] = {}
            header_data["ionospheric_corrections"][iono_type] = iono_values
        elif "TIME SYSTEM CORR" in line:
            time_corr_values = line[5:].strip().split()
            header_data["time_system_corr"] = time_corr_values
        elif "LEAP SECONDS" in line:
            header_data["leap_seconds"] = line[:6].strip()
        elif "END OF HEADER" in line:
            break
    return header_data


def parse_nav_observations(lines):
    observation_data = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("I"):
            prn = lines[i][:3].strip()
            epoch_year = int(lines[i][3:7].strip())
            epoch_month = int(lines[i][8:10].strip())
            epoch_day = int(lines[i][11:13].strip())
            epoch_hour = int(lines[i][14:16].strip())
            epoch_minute = int(lines[i][17:19].strip())
            epoch_second = float(lines[i][20:23].strip())
            clock_bias = float(lines[i][23:42].strip())
            clock_drift = float(lines[i][42:61].strip())
            clock_drift_rate = float(lines[i][61:80].strip())
            # Read additional lines for full observation record
            obs_data = [clock_bias, clock_drift, clock_drift_rate]
            i += 1
            while i < len(lines) and not lines[i].startswith("I"):
                obs_data.extend(
                    [
                        float(lines[i][23:42].strip()),
                        float(lines[i][42:61].strip()),
                        float(lines[i][61:80].strip()),
                    ]
                )
                i += 1
            observation_data.append(
                {
                    "PRN": prn,
                    "Epoch Year": epoch_year,
                    "Epoch Month": epoch_month,
                    "Epoch Day": epoch_day,
                    "Epoch Hour": epoch_hour,
                    "Epoch Minute": epoch_minute,
                    "Epoch Second": epoch_second,
                    "Clock Bias": obs_data[0],
                    "Clock Drift": obs_data[1],
                    "Clock Drift Rate": obs_data[2],
                    "Additional Data": obs_data[3:],
                }
            )
        else:
            i += 1
    return observation_data


def parse_nav_file(file_path):
    with open(file_path, "r") as file:
        lines = file.readlines()

    # Extract header
    header_lines = [line for line in lines if "END OF HEADER" not in line]
    header_data = parse_nav_header(header_lines)

    # Extract observation data
    observation_lines = lines[len(header_lines) :]
    observation_data = parse_nav_observations(observation_lines)

    # Create DataFrame for observation data
    obs_df = pd.DataFrame(observation_data)

    return {"header": header_data, "observations": obs_df}


# File selection dialog
Tk().withdraw()  # Prevent Tkinter root window from appearing
file_path = askopenfilename(
    title="Select RINEX Navigation File",
    filetypes=[("RINEX Navigation Files", "*.24N"), ("All Files", "*.*")],
)

# Process the file and get the extracted data
rinex_data = parse_nav_file(file_path)

# Display the header information
print("Header Information:")
for key, value in rinex_data["header"].items():
    print(f"{key}: {value}")

# Display the first few rows of the observations
print("\nObservation Data:")
print(rinex_data["observations"].head())

# Save observations to a new file
output_file_path = "processed_nav_data.csv"
rinex_data["observations"].to_csv(output_file_path, index=False)
print(f"\nProcessed observation data saved to {output_file_path}")
