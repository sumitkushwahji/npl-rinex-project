import re
import pandas as pd

def parse_rinex_nav_file(file_path):
    metadata = {}
    navigation_data = []

    with open(file_path, "r") as file:
        lines = file.readlines()

        header_end = False
        for i, line in enumerate(lines):
            if "END OF HEADER" in line:
                header_end = True
                header_end_index = i + 1
                break
            elif "RINEX VERSION / TYPE" in line:
                metadata["version"] = line[:9].strip()
                metadata["file_type"] = line[20:40].strip()
            elif "PGM / RUN BY / DATE" in line:
                metadata["program"] = line[:20].strip()
                metadata["run_by"] = line[20:40].strip()
                metadata["date"] = line[40:60].strip()
            elif "ION ALPHA" in line:
                metadata["ion_alpha"] = [float(x) for x in line[2:].split()[:4]]
            elif "ION BETA" in line:
                metadata["ion_beta"] = [float(x) for x in line[2:].split()[:4]]
            elif "DELTA-UTC: A0,A1,T,W" in line:
                metadata["delta_utc"] = [float(x) for x in line[3:].split()[:4]]
            elif "LEAP SECONDS" in line:
                metadata["leap_seconds"] = int(line.split()[0])

        if header_end:
            nav_lines = lines[header_end_index:]
            num_lines_per_record = 8  # Typically 8 lines per satellite record in a GPS RINEX Nav file
            for i in range(0, len(nav_lines), num_lines_per_record):
                record_lines = nav_lines[i:i + num_lines_per_record]

                # Print the first line for debugging purposes
                print(f"Record line 0: {record_lines[0].strip()}")

                # First line contains PRN and epoch
                try:
                    prn = record_lines[0][:3].strip()
                    year = int(record_lines[0][4:8].strip())  # Assuming 2000+ for RINEX 3
                    month = int(record_lines[0][9:11].strip())
                    day = int(record_lines[0][12:14].strip())
                    hour = int(record_lines[0][15:17].strip())
                    minute = int(record_lines[0][18:20].strip())
                    second_str = record_lines[0][21:23].strip()
                    second = float(second_str.replace(" ", "").replace("0", "", 1))
                except ValueError as e:
                    print(f"Error parsing epoch data: {e} | Line: {record_lines[0]}")
                    continue

                epoch = f"{year}-{month:02}-{day:02} {hour:02}:{minute:02}:{second:05.2f}"

                # SV clock data
                try:
                    sv_clock_bias = float(record_lines[0][23:42].strip())
                    sv_clock_drift = float(record_lines[0][43:61].strip())
                    sv_clock_drift_rate = float(record_lines[0][62:80].strip())
                except ValueError as e:
                    print(f"Error parsing SV clock data: {e}")
                    continue

                # Additional ephemeris data from following lines
                try:
                    nav_record = {
                        "PRN": prn,
                        "Epoch": epoch,
                        "SV Clock Bias": sv_clock_bias,
                        "SV Clock Drift": sv_clock_drift,
                        "SV Clock Drift Rate": sv_clock_drift_rate,
                        "IODE": float(record_lines[1][4:23].strip()),
                        "Crs": float(record_lines[1][23:42].strip()),
                        "Delta n": float(record_lines[1][42:61].strip()),
                        "M0": float(record_lines[1][61:80].strip()),
                        "Cuc": float(record_lines[2][4:23].strip()),
                        "e": float(record_lines[2][23:42].strip()),
                        "Cus": float(record_lines[2][42:61].strip()),
                        "sqrt(A)": float(record_lines[2][61:80].strip()),
                        "Toe": float(record_lines[3][4:23].strip()),
                        "Cic": float(record_lines[3][23:42].strip()),
                        "OMEGA0": float(record_lines[3][42:61].strip()),
                        "Cis": float(record_lines[3][61:80].strip()),
                        "i0": float(record_lines[4][4:23].strip()),
                        "Crc": float(record_lines[4][23:42].strip()),
                        "omega": float(record_lines[4][42:61].strip()),
                        "OMEGA DOT": float(record_lines[4][61:80].strip()),
                        "IDOT": float(record_lines[5][4:23].strip()),


                        
                        "IRN Week": float(record_lines[5][42:61].strip()),
                       
                        "SV Accuracy": float(record_lines[6][4:23].strip()),
                        "SV Health": float(record_lines[6][23:42].strip()),
                        "TGD": float(record_lines[6][42:61].strip()),
                       
                        "Transmission Time": float(record_lines[7][4:23].strip()),
                   
                    }
                except ValueError as e:
                    print(f"Error parsing ephemeris data: {e}")
                    continue

                navigation_data.append(nav_record)

    nav_df = pd.DataFrame(navigation_data)
    return {"metadata": metadata, "navigation": nav_df}

file_path = "ACCO0010.24N"
rinex_data = parse_rinex_nav_file(file_path)

print("Metadata:")
for key, value in rinex_data["metadata"].items():
    if isinstance(value, list):
        value = ", ".join(map(str, value))
    print(f"{key.replace('_', ' ').title()}: {value}")

print("\nNavigation Data:")
print(rinex_data["navigation"].head())

output_file_path = "processed_rinex_navigation_data.csv"
rinex_data["navigation"].to_csv(output_file_path, index=False)
print(f"\nProcessed navigation data saved to {output_file_path}")
