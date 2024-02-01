# myriad_utils_py
This repository contains the Python version of the myriad utilities designed to assist with spacecraft modeling and analysis on the Myriad cluster.
*Note:* These instructions assume that you have followed the instructions in the [UCL Raditiation Force Modelling Wiki](https://ucl-sgnl.github.io/) and have a working version of `srp_trr` compiled on in your Myriad home directory.

The general workflow is as follows:

## Preparing Your Spacecraft Model
Your spacecraft model should be a `.txt` file named after the mission ID and contained within a folder also named after the mission ID.

### Copying Files to Myriad
Here are the steps to prepare and transfer your files to the Myriad cluster:
1. **Copy Spacecraft Model to Myriad:**

```bash
scp -r /your/file/directory/{MISSION_ID}/ {UCL_ID}@myriad.rc.ucl.ac.uk:/home/{UCL_ID}/
```
The folder above should contain the spacecraft model and it should be named `MISSION_ID.txt`

2. **Copy myriad_utils_py to Myriad:**

to copy myriad_utils_py to the home directory on myriad:
```bash
scp -r /Users/charlesc/Documents/GitHub/myriad_utils_py {UCL_ID}@myriad.rc.ucl.ac.uk:/home/{UCL_ID}/
```
3. **Prepare the Working Directory:**
- Move the main script out of the `myriad_utils_py` directory into the home directory:
```bash
cp myriad_utils_py/set_and_run.py ../
```
- Move the resources folder out of the `myriad_utils_py` directory into the home directory:
```bash
cp -r myriad_utils_py/res ../
```
## Running the Utilities
To submit jobs, check job status, or combine output files, use the `set_and_run.py` script as follows:

1. **Submit Jobs:**
simply follow the prompts to submit jobs. The script will automatically create the necessary folders and files in Scratch. The script will also automatically generate the `paramFile.txt` file for each job. The `paramFile.txt` file contains the parameters for each job, including the spacecraft mass, pixel spacing, and emissivity. The `paramFile.txt` file is used by the `run.py` script to run the jobs.
```bash
python3 set_and_run.py
Enter the mission ID: {MISSION_ID}
Enter mode (submit/check/combine): submit
Enter the mass of the spacecraft: 1663
Enter the number of jobs: 10000
Enter the type of modelling required (0 for SRP, 1 for SRP+TRR, 2 for TRR): 0
Enter the pixel array orientation scheme (0 for EPS angles, 1 for spiral points): 1
Enter the pixel spacing of array (m): 0.001
Include secondary reflections? (Y or N): N
Enter the MLI emissivity for TRR models: 0.0
```

2. **Check Jobs Ran Successfully:**
This will check the status of the jobs and ensure that they ran successfully. If any jobs failed, the script will print a message to the console.
```bash
python3 set_and_run.py
Enter the mission ID: {MISSION_ID}
Enter mode (submit/check/combine): check
```

3. **Combine Output Files:**
This will combine all of the output files into a single file called `combined_output.txt` in the `outputFiles` folder. This file can then be downloaded to your local machine for analysis.
```bash
python3 set_and_run.py
Enter the mission ID: {MISSION_ID}
Enter mode (submit/check/combine): combine
number of files to combine: 10000
```

### Retrieving Combined Output File
To download the combined output file to your local machine:
```bash
❯ scp {UCL_ID}@myriad.rc.ucl.ac.uk:/home/{UCL_ID}/Scratch/{MISSION_ID}/spiralPoints/outputFiles/combined_output.txt /some/local/directory
```

## Important Notes
- This utility version is set up only for spiral points.
- A Scratch directory is included for local edits, allowing for file path retention without needing to push code to Myriad repeatedly. This is not the myriad scratch directory that the jobs will actually be run into.
- Run `set_and_run.py` outside of the `myriad_utils_py` directory to avoid path issues.
- After submitting jobs, inspect the `outputFiles` and `paramFiles` folders to verify that your jobs are running as expected. Most useful error messages with appear here.
