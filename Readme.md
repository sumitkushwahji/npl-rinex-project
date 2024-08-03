# RINEX Data Visualization Project

## Overview

This project involves parsing RINEX files and visualizing GPS observation data using Dash and Plotly. The application allows users to filter and visualize data based on observation type and satellite PRN. It also includes calculations for L1 and L2 values based on the provided frequency data.

## Signal Carrier Frequency Bandwidth

- **SPS – L5**: 1176.45 MHz, 24 MHz (1164.45 - 1188.45 MHz)
- **SPS – S**: 2492.028 MHz, 16.5 MHz (2483.50 - 2500.00 MHz)

## Documents

- [Document Link](https://nbmg.unr.edu/staff/pdfs/Blewitt_GL017i003p00199.pdf)
- [IRNSS ICD Document](https://www.isro.gov.in/media_isro/pdf/Publications/Vispdf/Pdf2017/irnss_sps_icd_version1.1-2017.pdf)
- [GNSS-RINEX-FORMAT](https://gage.upc.edu/en/learning-materials/library/gnss-format-descriptions)

## Getting Started

### Prerequisites

- Python 3.6 or higher
- Required Python packages: `dash`, `plotly`, `pandas`, `re`

### Installation

1. Clone the repository:

   ```bash
   git clone https://your-repository-url.git
   ```
