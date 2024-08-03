import re
import pandas as pd


def parse_rinex_file(file_path):
    metadata = {}
    observation_data = []

    with open(file_path, "r") as file:
        lines = file.readlines()

        header_end = False
        obs_types = []
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
            elif "MARKER NAME" in line:
                metadata["marker_name"] = line[:60].strip()
            elif "MARKER NUMBER" in line:
                metadata["marker_number"] = line[:60].strip()
            elif "MARKER TYPE" in line:
                metadata["marker_type"] = line[:60].strip()
            elif "OBSERVER / AGENCY" in line:
                metadata["observer"] = line[:20].strip()
                metadata["agency"] = line[20:40].strip()
            elif "REC # / TYPE / VERS" in line:
                metadata["receiver_number"] = line[:20].strip()
                metadata["receiver_type"] = line[20:40].strip()
                metadata["receiver_version"] = line[40:60].strip()
            elif "ANT # / TYPE" in line:
                metadata["antenna_number"] = line[:20].strip()
                metadata["antenna_type"] = line[20:40].strip()
            elif "APPROX POSITION XYZ" in line:
                metadata["approx_position_xyz"] = [float(x) for x in line.split()[:3]]
            elif "ANTENNA: DELTA H/E/N" in line:
                metadata["antenna_delta_hen"] = [float(x) for x in line.split()[:3]]
            elif "SYS / # / OBS TYPES" in line:
                parts = line.split()
                num_obs_types = int(parts[1])
                obs_types_line = parts[2:]
                while len(obs_types_line) < num_obs_types:
                    i += 1
                    obs_types_line.extend(lines[i].split())
                obs_types = obs_types_line[:num_obs_types]
            elif "SIGNAL STRENGTH UNIT" in line:
                metadata["signal_strength_unit"] = line[:60].strip()
            elif "INTERVAL" in line:
                metadata["interval"] = float(line[:10].strip())
            elif "TIME OF FIRST OBS" in line:
                metadata["time_of_first_obs"] = line[:40].strip()
            elif "TIME OF LAST OBS" in line:
                metadata["time_of_last_obs"] = line[:40].strip()

        obs_types_specs = {
            "C5C": (14, 1, 1),
            "L5C": (16, 1, 1),
            "D5C": (12, 1, 1),
            "S5C": (14, 1, 1),
            "C9C": (14, 1, 1),
            "L9C": (16, 1, 1),
            "D9C": (12, 1, 1),
            "S9C": (14, 1, 1),
        }

        if header_end:
            observation_lines = lines[header_end_index:]
            current_epoch = None

            for line in observation_lines:
                if re.match(r"^\s*>\s*", line):
                    epoch_parts = line[1:].strip().split()
                    year, month, day, hour, minute = epoch_parts[:5]
                    second = float(epoch_parts[5])
                    epoch_flag = int(epoch_parts[6])
                    num_satellites = int(epoch_parts[7])
                    receiver_clock_offset = (
                        float(epoch_parts[8]) if len(epoch_parts) > 8 else None
                    )
                    current_epoch = f"{year}-{month.zfill(2)}-{day.zfill(2)} {hour.zfill(2)}:{minute.zfill(2)}:{second:02.0f}"
                else:
                    if current_epoch:
                        index = 0
                        prn = line[index : index + 3].strip()
                        index += 3

                        for obs_type in obs_types:
                            value_length, lol_length, ssi_length = obs_types_specs[
                                obs_type
                            ]
                            value = line[index : index + value_length].strip()
                            value = value.lstrip("0")  # Remove leading zeros
                            index += value_length
                            lol = line[index : index + lol_length].strip()
                            index += lol_length
                            ssi = line[index : index + ssi_length].strip()
                            index += ssi_length

                            observation_data.append(
                                {
                                    "Epoch": current_epoch,
                                    "Epoch Flag": epoch_flag,
                                    "Epoch Satellite Number": num_satellites,
                                    "Receiver Clock Offset": receiver_clock_offset,
                                    "Obs_Type": obs_type,
                                    "PRN": prn,
                                    "Value": value,
                                    "LoL": lol,
                                    "SSI": ssi,
                                }
                            )

    obs_df = pd.DataFrame(observation_data)
    return {"metadata": metadata, "observations": obs_df}


file_path = "ACCO0020.24O"
rinex_data = parse_rinex_file(file_path)

print("Metadata:")
for key, value in rinex_data["metadata"].items():
    if isinstance(value, list):
        value = ", ".join(map(str, value))
    elif isinstance(value, dict):
        value = (
            f"{value['system']} {value['num_obs_types']} {' '.join(value['obs_types'])}"
        )
    print(f"{key.replace('_', ' ').title()}: {value}")

print("\nObservations:")
print(rinex_data["observations"].head())

output_file_path = "processed_rinex_data.csv"
rinex_data["observations"].to_csv(output_file_path, index=False)
print(f"\nProcessed observation data saved to {output_file_path}")