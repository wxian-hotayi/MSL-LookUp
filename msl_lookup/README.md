# MSL Lookup Tool

Desktop application to batch-lookup Moisture Sensitivity Level (MSL) for electronic components.

## Setup

### 1. Get Mouser API Key (free)
1. Go to https://www.mouser.com/api
2. Sign up / log in
3. Generate your free API key

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set API Key
```bash
# Windows
set MOUSER_API_KEY=your_api_key_here

# Linux/Mac
export MOUSER_API_KEY=your_api_key_here
```

### 4. Run
```bash
python main.py
```

## Usage
1. Click "Browse..." to select an Excel/CSV file with MPN column
2. Click "Load File" to preview data
3. Click "Find MSL" to lookup MSL for all parts
4. Click "Export" to save results

## Input File Format
Excel or CSV with a column containing Maker Part Numbers (MPN).
Supported column names: `MPN`, `Maker Part No`, `Part Number`, `PartNo`, or `Part`

## Output
Original data + `MSL` column appended. Parts with no MSL found are left blank.
