def parse_rinex_file(file_path):
    """
    Parse a RINEX file and extract its metadata and observation types.

    :param file_path: Path to the RINEX file.
    :return: A dictionary containing extracted data.
    """
    metadata = {}

    with open(file_path, "r") as file:
        for line in file:
            # Extract information based on the keyword found at the end of each line
            if "RINEX VERSION / TYPE" in line:
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
                metadata["observation_types"] = line[6:].strip().split()
            elif "SIGNAL STRENGTH UNIT" in line:
                metadata["signal_strength_unit"] = line[:60].strip()
            elif "INTERVAL" in line:
                metadata["interval"] = float(line[:10].strip())
            elif "TIME OF FIRST OBS" in line:
                metadata["time_of_first_obs"] = line[:40].strip()
            elif "TIME OF LAST OBS" in line:
                metadata["time_of_last_obs"] = line[:40].strip()

    return metadata


# Correct the file path
path = r"C:\Users\Admin\Desktop\project\Bharat sir\npl-rinex-project\ACCO0020.24O"

# Process the file and print the extracted metadata
rinex_metadata = parse_rinex_file(path)

# Format and display the metadata
for key, value in rinex_metadata.items():
    if isinstance(value, list):
        value = ", ".join(map(str, value))
    print(f"{key.replace('_', ' ').title()}: {value}")
