################# The following Code just reads the RINEX 4.0 version data. ################


import numpy as np
from datetime import datetime
import pandas as pd


class Receiver:
    def __init__(self):
        self.rinex_version = None  # Placeholder for the RINEX format version
        self.observation_type = ""  # Type of observation data
        self.system_type = (
            ""  # Indicates if the data is mixed or specific to a GNSS system
        )
        self.receiver_number = ""  # Receiver Number
        self.receiver_type = ""  # Receiver Type
        self.receiver_version = ""  # Receiver Version
        self.observations = np.array([])
        self.epochs = []
        self.gnss_systems = []  # List of GNSS systems observed
        self.observation_codes = (
            {}
        )  # Dict to store observation types for each GNSS system
        self.marker_name = ""
        self.marker_number = ""
        self.observer = ""  # Name of the observer
        self.agency = ""  # Name of the agency
        self.antenna_height = None  # Height of the ARP above the marker
        self.antenna_east_eccen = None  # Antenna East eccentricity
        self.antenna_north_eccen = None  # Antenna North eccentricity
        self.approx_position_xyz = (0.0, 0.0, 0.0)
        self.antenna_phase_center = (
            {}
        )  # Store phase center info by GNSS system and observation code
        self.antenna_number = ""  # Antenna Number
        self.antenna_type = ""  # Antenna Type
        self.program_run_info = ("", "", "")
        self.phase_shifts = {}  # Dict to store phase shifts for each GNSS system
        self.leap_seconds = None  # Placeholder for the number of leap seconds
        self.num_of_satellites = 0  # New
        self.interval = (
            None  # 0.0  # Use None as a default value to indicate it's not set
        )
        self.time_of_first_obs = None  # Placeholder for the start time of observations
        self.time_of_last_obs = None  # Placeholder for the end time of observations
        self.time_system = None  # Time reference system
        self.glonass_slot_frq_num = {}  # Store GLONASS slot and frequency numbers
        self.satellite_obs_counts = (
            {}
        )  # property to hold the number of observations for each satellite; Dict to store observation counts by type for each PRN
        self.scale_factors = {}  # Store scale factors by GNSS system
        self.rcv_clock_offs_appl = 0  # Default set to "not applied"
        self.prn_obs_counts = {}  # Key: PRN, Value: dict of observation type counts
        self.glonass_code_phase_bias = {}  # Store GLONASS code/phase bias corrections
        self.obs_data = {}  # Store Observation data for each GNSS system
        self.observation_data = {}  # Store the complete observation data

    def _initialize_obs_data(self):
        """Initializes empty DataFrames for each GNSS system based on parsed header info."""

        for system in self.gnss_systems:
            obs_codes = self.observation_codes[system]

            # Ensure prns is not empty to avoid creating an index with no levels.
            prns = [prn for prn in self.prn_obs_counts if prn.startswith(system)]
            if not prns:
                # print(f"No PRNs found for system {system}. Skipping DataFrame initialization.")
                continue

            # Initialize columns ensuring 'rx_clk_off' is handled separately to avoid being treated as a level in MultiIndex.
            columns = [("rx_clk_off", "")] + [
                (obs_type, prn) for obs_type in obs_codes for prn in prns
            ]

            # Use MultiIndex for columns to enable grouping by observation type.
            # Note: Including a dummy empty string for 'rx_clk_off' to match the two-level structure.
            multi_index = pd.MultiIndex.from_tuples(
                columns, names=["Observation", "Satellite"]
            )

            # Initialize DataFrame for the current GNSS system.
            self.obs_data[f"{system}_obs"] = pd.DataFrame(columns=multi_index)

    def _parse_rinex_version_type_line(self, line):
        """Parses the 'RINEX VERSION / TYPE' line to extract version, observation type, and system type."""
        self.rinex_version = float(
            line[:9].strip()
        )  # RINEX version as a floating-point number
        self.observation_type = line[20:40].strip()  # Extract the observation data type

        # Extract the system type character and map it to the full name or abbreviation for clarity
        system_char = line[
            40:41
        ].strip()  # Extract the single character indicating the system type
        system_map = {
            "G": "GPS",
            "R": "GLONASS",
            "S": "SBAS",
            "E": "Galileo",
            "J": "QZSS",
            "C": "BDS",
            "I": "IRNSS",
            "M": "Mixed",
        }
        self.system_type = system_map.get(
            system_char, system_char
        )  # Default to the char if not found

    def _parse_time_line(self, time_str):
        """Parses a datetime line from the RINEX header and returns a numpy datetime64 object."""
        # Split the time string to separate the fractional seconds
        parts = time_str.split(".")
        base_time_str = parts[0]  # Base datetime string without fractional seconds
        fractional_seconds_str = (
            "0." + parts[1] if len(parts) > 1 else "0"
        )  # Fractional seconds as a string

        # Parse the base datetime string
        dt = datetime.strptime(base_time_str, "%Y %m %d %H %M %S")

        # Convert fractional seconds string to a float, then to nanoseconds for numpy timedelta64
        fractional_seconds = float(fractional_seconds_str)
        nanoseconds = int(fractional_seconds * 1e9)

        # Combine and convert to numpy datetime64
        np_dt = np.datetime64(dt) + np.timedelta64(nanoseconds, "ns")
        return np_dt

    def _parse_phase_shifts_line(self, line):
        """Parses a 'SYS / PHASE SHIFTS' line."""
        parts = line.split()
        gnss_system = parts[0]
        obs_code = parts[1]
        # Safely parse the phase shift value, defaulting to 0.0 if not present or not a float
        try:
            phase_shift = (
                float(parts[2])
                if len(parts) > 2 and parts[2].replace(".", "", 1).isdigit()
                else 0.0
            )
        except ValueError:
            phase_shift = 0.0  # Default phase shift if conversion fails

        # Determine if there are specified satellites (depends on the presence of a numeric value indicating their count)
        num_satellites = 0
        satellites = []
        if len(parts) > 3 and parts[3].isdigit():
            num_satellites = int(parts[3])
            satellites = parts[4 : 4 + num_satellites]

        # Initialize the dictionary structure for the GNSS system if not present
        if gnss_system not in self.phase_shifts:
            self.phase_shifts[gnss_system] = {}

        # Store the phase shift information for the observation code
        self.phase_shifts[gnss_system][obs_code] = {
            "phase_shift": phase_shift,
            "satellites": satellites,
        }

    def _parse_prn_obs_line(self, epoch, line):
        """Parses observation data for each PRN, aligning the observed values with the expected GNSS observation types."""
        prn = line[:3].strip()
        gnss_system = prn[0]
        obs_data = {}

        # Ensure we map observation data to their respective types for the GNSS system of the PRN
        if gnss_system in self.observation_codes:
            obs_types = self.observation_codes[gnss_system]

            # Prepare to extract each data point based on the known format size
            data_start = 3
            data_length = 16  # Assuming 14 for the value + 1 for lock + 1 for strength
            for obs_type in obs_types:
                data_end = data_start + data_length
                data_point = line[data_start:data_end].strip()

                if (
                    len(data_point) > 2
                ):  # There's enough data for at least the value and indicators
                    value = float(data_point[:-2]) if data_point[:-2].strip() else None
                    loss_lock = (
                        int(data_point[-2]) if data_point[-2].isdigit() else None
                    )
                    signal_strength = (
                        int(data_point[-1]) if data_point[-1].isdigit() else None
                    )
                else:
                    value, loss_lock, signal_strength = None, None, None

                obs_data[obs_type] = {
                    "value": value,
                    "loss_of_lock": loss_lock,
                    "signal_strength": signal_strength,
                }
                data_start = data_end  # Move to the start of the next data point

            # Store this PRN's data under its corresponding epoch and system
            if epoch not in self.observation_data:
                self.observation_data[epoch] = {}
            if gnss_system not in self.observation_data[epoch]:
                self.observation_data[epoch][gnss_system] = {}
            self.observation_data[epoch][gnss_system][prn] = obs_data
            # print("observation data: ")
            # print(self.observation_data)
        else:
            print(
                f"Warning: GNSS system '{gnss_system}' for PRN {prn} not found in observation types."
            )

    def _parse_antenna_phase_center_line(self, line):
        """Parses an 'ANTENNA: PHASECENTER' line."""
        parts = line.split()
        gnss_system = parts[0]  # GNSS system code
        obs_code = parts[1]  # Observation code
        # Extract the North, East, Up phase center positions
        north, east, up = float(parts[2]), float(parts[3]), float(parts[4])

        # Initialize the dictionary for the GNSS system if not present
        if gnss_system not in self.antenna_phase_center:
            self.antenna_phase_center[gnss_system] = {}

        # Store the phase center info for the observation code
        self.antenna_phase_center[gnss_system][obs_code] = {
            "north": north,
            "east": east,
            "up": up,
        }

    def _parse_glonass_code_phase_bias_line(self, line):
        """Parses a 'GLONASS COD/PHS/BIS' line."""
        # Initial split of the line based on whitespace
        parts = line.strip().split()

        # Iterate over the parts in pairs (identifier, bias), excluding the last descriptor part
        for i in range(
            0, len(parts) - 2, 2
        ):  # Excluding 'GLONASS COD/PHS/BIS' by reducing loop range
            signal_identifier = parts[i]
            # Check if the next part is a number (float) before attempting conversion
            if parts[i + 1].replace(".", "", 1).isdigit():
                bias_correction = float(parts[i + 1])
            else:
                bias_correction = None  # Default to None if not a valid float

            # Store the bias correction for the signal identifier
            self.glonass_code_phase_bias[signal_identifier] = bias_correction

    def _parse_epoch_line(self, line):
        """Parses an epoch line, accounting for fractional seconds."""
        parts = line[2:].split()  # Splitting from position 2 to skip '> '
        year, month, day, hour, minute = map(int, parts[:5])
        second = float(parts[5])  # Fractional seconds are now correctly parsed as float
        epoch = np.datetime64(
            f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{int(second):02d}"
        )
        # Note: Fractional part of the seconds is ignored in the final datetime64 object here; adjust if needed
        return epoch

    def import_data(self, filepath):
        """Imports RINEX observation data from a given file, parsing the header in detail."""
        current_prn = None
        obs_data_start = False
        obs_counts = []  # Initialize obs_counts here to avoid UnboundLocalError
        current_epoch = None

        with open(filepath, "r") as file:
            for line in file:
                if "END OF HEADER" in line:
                    # Initialize Empty DataFrames based on parsed header data
                    obs_data_start = True
                    self._initialize_obs_data()  # Initialize empty DataFrames after parsing the header
                    # No need to break; continue reading the file for observation data

                if line.startswith(">"):
                    obs_data_start = True  # Some of the files doesnt have the line 'END OF HEADER' in their RINEX format

                if not obs_data_start:  # If the observation data not sarted yet

                    header_label = line[60:].strip()

                    if header_label == "RINEX VERSION / TYPE":
                        self._parse_rinex_version_type_line(line)

                    elif (
                        header_label == "PGM / RUN BY / DATE"
                    ):  # Name of the programm , agency creating the current file, date of creation
                        self.program_run_info = (
                            line[:20].strip(),
                            line[20:40].strip(),
                            line[40:60].strip(),
                        )

                    elif header_label == "MARKER NAME":  # Name of the Antenna Marker
                        self.marker_name = line[:20].strip()

                    elif header_label == "MARKER NUMBER":  # Number of Antenna Marker
                        self.marker_number = line[:20].strip()

                    elif (
                        header_label == "OBSERVER / AGENCY"
                    ):  # Name of the observer and Name of the Agency
                        # Extract and store the observer and agency names
                        self.observer = line[:20].strip()  # Observer name
                        self.agency = line[20:60].strip()  # Agency name

                    elif header_label == "APPROX POSITION XYZ":
                        # Extract and store the X, Y, Z coordinates
                        x_coord = float(line[0:14].strip())
                        y_coord = float(line[14:28].strip())
                        z_coord = float(line[28:42].strip())
                        self.approx_position_xyz = (x_coord, y_coord, z_coord)

                    elif header_label == "ANTENNA: DELTA H/E/N":
                        # Extract and store the antenna height and eccentricity
                        parts = line[
                            :43
                        ].split()  # Assume up to 43 characters for the three values
                        if len(parts) >= 3:
                            self.antenna_height = float(
                                parts[0]
                            )  # Antenna height above the marker
                            self.antenna_east_eccen = float(parts[1])
                            self.antenna_north_eccen = float(parts[2])

                    elif header_label == "ANT # / TYPE":
                        # Extract and store the antenna number and type
                        self.antenna_number = line[:20].strip()  # Antenna Number
                        self.antenna_type = line[20:40].strip()  # Antenna Type

                    elif header_label == "REC # / TYPE / VERS":
                        # Extract and store the receiver number, type, and version
                        self.receiver_number = line[:20].strip()  # Receiver Number
                        self.receiver_type = line[20:40].strip()  # Receiver Type
                        self.receiver_version = line[40:60].strip()  # Receiver Version

                    elif (
                        header_label == "ANTENNA: PHASECENTER"
                    ):  # Parsing for "ANTENNA: PHASECENTER" lines
                        self._parse_antenna_phase_center_line(line)

                    elif (
                        header_label == "SYS / # / OBS TYPES"
                        or header_label.startswith("SYS / # / OBS TYPES")
                    ):
                        if line[0] in [
                            "G",
                            "R",
                            "E",
                            "C",
                            "S",
                            "I",
                        ]:  # GNSS system identifiers
                            system = line[0]
                            num_obs_types = int(
                                line.split()[1]
                            )  # Extract the number of observation types securely
                            self.current_gnss_system = system
                            self.observation_codes[system] = []
                            self.obs_types_remaining = num_obs_types

                            # Start extracting observation codes after the number
                            start_index = line.find(str(num_obs_types)) + len(
                                str(num_obs_types)
                            )
                            obs_types = line[start_index:].strip().split()

                        else:
                            # Handle continuation line when there is no GNSS system identifier but obs types are still expected
                            obs_types = line.strip().split()

                        # Process observation types, ensuring the count is respected
                        if self.current_gnss_system and self.obs_types_remaining > 0:
                            num_to_add = min(self.obs_types_remaining, len(obs_types))
                            self.observation_codes[self.current_gnss_system].extend(
                                obs_types[:num_to_add]
                            )
                            self.obs_types_remaining -= num_to_add

                            if self.obs_types_remaining <= 0:
                                print(
                                    f"Final observation codes for {self.current_gnss_system}: {self.observation_codes[self.current_gnss_system]}"
                                )
                                self.current_gnss_system = None  # Reset after all observation types for current system are read

                    elif header_label == "SYS / PHASE SHIFT":

                        self._parse_phase_shifts_line(line)

                    elif header_label == "GLONASS SLOT / FRQ #":
                        # The first character is the number of satellites, which is not always explicitly needed for parsing
                        entries = (
                            line[1:60].strip().split()
                        )  # Strip and split the rest of the line by spaces

                        for entry in entries:
                            if entry.startswith(
                                "R"
                            ):  # Check if the entry is for a GLONASS satellite
                                slot_number = int(entry[1:3])  # Extract the slot number
                                frq_number = (
                                    int(entry[3:]) if len(entry) > 3 else None
                                )  # Extract the frequency number if available
                                self.glonass_slot_frq_num[slot_number] = frq_number

                    elif header_label == "LEAP SECONDS":
                        # Extract and store the number of leap seconds as trsmitted by GPS Almanc information
                        self.leap_seconds = int(line[:6].strip())

                    elif header_label == "# OF SATELLITES":
                        # Number of satellites, for which observations are stored in the file.
                        self.num_of_satellites = int(line[:6].strip())

                    elif header_label == "INTERVAL":
                        self.interval = float(line[:10].strip())

                    elif header_label == "TIME OF FIRST OBS":
                        # Parse and store the start time and time system
                        self.time_of_first_obs = self._parse_time_line(
                            line[:43].strip()
                        )
                        self.time_system = line[48:51].strip()

                    elif header_label == "TIME OF LAST OBS":
                        # Parse and store the end time
                        self.time_of_last_obs = self._parse_time_line(line[:43].strip())
                        # Assuming the time system is the same as specified in TIME OF FIRST OBS, no need to parse again

                    elif header_label == "RCV CLOCK OFFS APPL":
                        # Parse and store the receiver clock offset application flag
                        self.rcv_clock_offs_appl = int(line[:6].strip())

                    elif (
                        header_label.startswith("SYS / SCALE FACTOR")
                        or header_label == "SYS / SCALE FACTOR"
                    ):
                        scale_info = line.split()  # Split the line into components
                        if line[0] in [
                            "G",
                            "R",
                            "E",
                            "C",
                            "S",
                            "I",
                        ]:  # If it's a new system identifier
                            system = scale_info[0]  # GNSS system
                            scale_factor = int(scale_info[1])  # Scale factor
                            self.current_gnss_system = (
                                system  # Update the current GNSS system
                            )
                            # Initialize or update scale factor for the current GNSS system
                            self.scale_factors[system] = scale_factor
                            # Observation types that the scale factor applies to, if listed on the same line
                            obs_types = scale_info[3:] if len(scale_info) > 3 else []
                            if system in self.observation_codes:
                                self.observation_codes[system].extend(obs_types)
                            else:
                                self.observation_codes[system] = obs_types
                        else:
                            # Continuation line for the current GNSS system's scale factor
                            if self.current_gnss_system:
                                obs_types_continued = line[3:60].strip().split()
                                self.observation_codes[self.current_gnss_system].extend(
                                    obs_types_continued
                                )

                    elif header_label == "PRN / # OF OBS" or current_prn is not None:
                        if (
                            line[0].strip() == ""
                        ):  # This checks if the line is a continuation line
                            # Continue accumulating obs_counts for the current PRN
                            additional_counts = [
                                int(part.strip())
                                for part in line.strip().split()
                                if part.strip().isdigit()
                            ]
                            obs_counts += additional_counts
                        else:
                            if (
                                current_prn
                            ):  # Process the previous PRN before moving to a new one
                                # Finalize observation counts for the current PRN
                                if (
                                    current_prn[0] in self.observation_codes
                                ):  # Ensure GNSS system is recognized
                                    obs_types = self.observation_codes[current_prn[0]]
                                    self.prn_obs_counts[current_prn] = dict(
                                        zip(obs_types, obs_counts)
                                    )

                            # Reset for a new PRN block
                            current_prn = line[0:3].strip()  # Extract the PRN code
                            obs_counts = [
                                int(part.strip())
                                for part in line[4:].strip().split()
                                if part.strip().isdigit()
                            ]

                        # Handle the end of the last PRN block after exiting the loop
                        if current_prn and current_prn[0] in self.observation_codes:
                            obs_types = self.observation_codes[current_prn[0]][
                                : len(obs_counts)
                            ]
                            self.prn_obs_counts[current_prn] = dict(
                                zip(obs_types, obs_counts)
                            )

                    elif (
                        header_label == "GLONASS COD/PHS/BIS"
                    ):  # Parsing for "GLONASS COD/PHS/BIS" line
                        self._parse_glonass_code_phase_bias_line(line)

                elif obs_data_start:  # Observation Data started
                    # check for multiple headers in the file
                    header_label = line[60:].strip()
                    if header_label == "RINEX VERSION / TYPE":
                        obs_data_start = False

                    if obs_data_start:
                        if line.startswith(">"):
                            # Parse the new epoch including fractional seconds
                            current_epoch = self._parse_epoch_line(line)
                            self.epochs.append(current_epoch)
                        else:
                            # Parse observation data
                            self._parse_prn_obs_line(current_epoch, line)

                            # satellite = line[:3].strip()
                            # measurements = line[3:].split()  # Assuming measurements are correctly handled as strings here
                            # if current_epoch:  # Ensure there's a valid current epoch
                            #     self.observations.append((current_epoch, satellite, measurements))
        # print("observation data: ")
        # print(self.observation_data)

    def delete_observation(self, epoch):
        """Deletes observations for a specific epoch."""
        self.observations = [obs for obs in self.observations if obs[0] != epoch]
        if epoch in self.epochs:
            self.epochs.remove(epoch)

    def append_observation(self, observation, epoch, gnss_system, observation_code):
        """Appends a new observation."""
        # This method should be refined based on how you define an observation's structure
        self.observations.append((epoch, gnss_system, observation))
        if gnss_system not in self.gnss_systems:
            self.gnss_systems.append(gnss_system)
        if gnss_system not in self.observation_codes:
            self.observation_codes[gnss_system] = [observation_code]
        elif observation_code not in self.observation_codes[gnss_system]:
            self.observation_codes[gnss_system].append(observation_code)


def export_irnss_data_to_file(receiver, filename):
    """Exports IRNSS observation data to a text file."""
    # Prepare a list to accumulate data
    all_data = []

    # Iterate over each epoch in the observation data
    for epoch, systems_data in receiver.observation_data.items():
        # Extract data for IRNSS system if available
        irnss_data = systems_data.get("I", {})
        # print(f"IRNSS data for epoch {epoch}: {irnss_data}")

        # Iterate over observation types and their data
        for prn, obs_types_data in irnss_data.items():
            for obs_type, data in obs_types_data.items():
                # Prepare a single row per observation
                all_data.append(
                    {
                        "Epoch": epoch,
                        "Obs_Type": obs_type,
                        "PRN": prn,
                        "Value": data.get("value"),
                        "LoL": data.get("loss_of_lock"),
                        "SSI": data.get("signal_strength"),
                    }
                )

    # Convert list to DataFrame
    if all_data:
        df = pd.DataFrame(all_data)
        # print(df.head())  # Print first few rows to check
        df.sort_values(["Epoch", "PRN", "Obs_Type"], inplace=True)

        # Write DataFrame to text file
        df.to_csv(filename, index=False, sep="\t")

        print(f"Data exported to {filename} successfully.")
    else:
        print("No IRNSS data available to export.")


# Example usage
receiver = Receiver()

receiver.import_data(
    "H:\\NavIC_Tri_band_Data\\ITBR2910\\ITBR2910.23O"
)  # Update the filepath accordingly

export_irnss_data_to_file(receiver, "irnss_observation_data.txt")

# Example to access IRNSS L1C data

# irnss_l1c = receiver.observation_data.get('I', {}).get('L1C', {})

# Example to access GPS L2P data
# gps_l2p = receiver.observation_data.get('G', {}).get('L2P', {})
