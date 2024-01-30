import os
import subprocess
import shutil
import time
# Constants

SCRATCH_DIR = "Scratch"
SRP_TRR_CLASSIC_PATH = "/srp_trr_classic/bin/srp_trr_classic"
RES_DIR = "res"
HOME_DIR = "."

def clear_directory(directory):
    """Empties out a directory."""
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

def wait_for_jobs_to_complete():
    """Waits for all submitted jobs to complete before proceeding."""
    print("Waiting for jobs to complete...")
    jobs_running = True
    while jobs_running:
        time.sleep(60)  # Check every minute
        result = subprocess.run(["qstat"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if not result.stdout.strip():
            jobs_running = False

def generate_directory_structure(base_dir, mission):
    """
    Generates the directory structure for the given mission.
    """
    output_dir = os.path.join(base_dir, mission, "spiralPoints", "outputFiles")
    param_dir = os.path.join(base_dir, mission, "spiralPoints", "paramFiles")

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(param_dir, exist_ok=True)

    return output_dir, param_dir

def generate_parameter_files(template_filename, output_prefix, num_files=10000):
    """
    Generates parameter files based on a template.

    :param template_filename: Path to the template file.
    :param output_prefix: Prefix for the output files.
    :param num_files: Number of parameter files to generate.
    """
    # Read the template file
    with open(template_filename, 'r') as template_file:
        template_content = template_file.readlines()

    # Generate parameter files
    for i in range(1, num_files + 1):
        output_filename = f"{output_prefix}{str(i).zfill(5)}.txt"
        with open(output_filename, 'w') as output_file:
            for line in template_content:
                if line.startswith("scheme"):
                    line = "scheme       = 1\n"
                elif line.startswith("k_s"):
                    line = f"k_start      = {i}\n"
                elif line.startswith("k_f"):
                    line = f"k_finish     = {i}\n"
                elif line.startswith("n_p"):
                    line = "n_points     = 10000\n"
                output_file.write(line)

def setup_environment(mission, mass, res_dir, home_dir):
    """
    Sets up the environment for UCL SRP force model computation.

    :param mission: Name of the mission.
    :param mass: Mass of the spacecraft.
    :param res_dir: Directory where resources are located.
    :param home_dir: Home directory path.
    """
    # Create necessary directories
    mission_dirs = [
        f"{mission}/force_models",
        f"{home_dir}/Scratch/{mission}/EPSprime/jobs",
        f"{home_dir}/Scratch/{mission}/EPSprime/outputFiles",
        f"{home_dir}/Scratch/{mission}/EPSprime/paramFiles",
        f"{home_dir}/Scratch/{mission}/EPSprime/stdout",
        f"{home_dir}/Scratch/{mission}/spiralPoints/jobs",
        f"{home_dir}/Scratch/{mission}/spiralPoints/outputFiles",
        f"{home_dir}/Scratch/{mission}/spiralPoints/paramFiles",
        f"{home_dir}/Scratch/{mission}/spiralPoints/stdout"
    ]
    for dir_path in mission_dirs:
        os.makedirs(dir_path, exist_ok=True)

    # Copy parameter file and update spacecraft mass
    shutil.copy(f"{res_dir}/parameters_template.txt", f"{home_dir}/{mission}/parameters.txt")
    with open(f"{home_dir}/{mission}/parameters.txt", 'r') as file:
        lines = file.readlines()

    # Update the line containing the spacecraft mass
    for i, line in enumerate(lines):
        if line.strip().startswith("// mass of spacecraft (kg)"):
            lines[i] = f"mass         = {mass}\n"
            break

    with open(f"{home_dir}/{mission}/parameters.txt", 'w') as file:
        file.writelines(lines)

def convert_line_endings_to_local(filename, output_prefix="local"):
    """
    Converts line endings in the file to Unix-style (LF) and writes to a new file.

    :param filename: The name of the file to be converted.
    :param output_prefix: The prefix for the output file.
    """
    with open(filename, 'r', newline=None) as f:
        content = f.read()
    
    new_content = content.replace('\r\n', '\n').replace('\r', '\n')
    with open(output_prefix + filename, 'w', newline='\n') as w:
        w.write(new_content)

def submit_jobs(srp_trr_classic_path, param_files_dir, spacecraft_model_file, output_files_dir, total_jobs=10000):
    """
    Submits jobs to the job scheduler and deletes the job scripts after submission.
    """
    for job_id in range(1, total_jobs + 1):
        job_script_filename = f"job_script_{str(job_id).zfill(5)}.sh"
        job_script = job_script_filename  # Temporary job script in the current directory
        param_file = f"{param_files_dir}/params{str(job_id).zfill(5)}.txt"
        output_file = f"{output_files_dir}/output{str(job_id).zfill(5)}.txt"  # Ensure this path is correct

        with open(job_script, "w") as file:
            file.write("#!/bin/bash\n")
            cmd = f"{srp_trr_classic_path} {param_file} {spacecraft_model_file} {output_file}\n"
            file.write(cmd)
        
        subprocess.run(["qsub", job_script])
        os.remove(job_script)  # Delete the job script after submission

def legion_check(output_dir, expected_files, logfile=None):
    """
    Checks the output of a Legion SRP job.

    :param output_dir: Directory where output files are stored.
    :param expected_files: Number of expected output files.
    :param logfile: Optional log file to write results to.
    """
    missing_files = []
    line_count_issues = []

    # Check for missing files
    for i in range(1, expected_files + 1):
        file_name = f"output{str(i).zfill(len(str(expected_files)))}.txt"
        file_path = os.path.join(output_dir, file_name)
        if not os.path.exists(file_path):
            missing_files.append(file_name)
        else:
            # Check line count
            with open(file_path, 'r') as file:
                lines = file.readlines()
                if len(lines) != 2:
                    line_count_issues.append((file_name, len(lines)))

    # Log results
    log_lines = [
        f"Number of output files returned: {expected_files - len(missing_files)}",
        f"Missing files: {missing_files}",
        f"Files with incorrect line count: {line_count_issues}"
    ]
    if logfile:
        with open(logfile, 'w') as log_file:
            log_file.write('\n'.join(log_lines))
    else:
        for line in log_lines:
            print(line)

    # Summary
    if not missing_files and not line_count_issues:
        summary = "No missing files, no repeated spiral points, and no error entries. Things check out."
    else:
        summary = "There is a problem with one or more output files."
    if logfile:
        with open(logfile, 'a') as log_file:
            log_file.write('\n' + summary)
    else:
        print(summary)

def legion_combine(output_dir, combined_output_file, expected_files):
    """
    Combines SRP output files into a single text file and sorts them.

    :param output_dir: Directory where output files are stored.
    :param combined_output_file: File path for the combined output.
    :param expected_files: Number of expected output files.
    """
    combined_data = []

    # Read data from each output file
    for i in range(1, expected_files + 1):
        file_name = f"output{str(i).zfill(len(str(expected_files)))}.txt"
        file_path = os.path.join(output_dir, file_name)
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                lines = file.readlines()[1:]  # Skip header line
                combined_data.extend(lines)

    combined_data.sort(key=lambda x: float(x.split()[0]), reverse=True)
 
    # Write combined data to a file
    with open(combined_output_file, 'w') as output_file:
        output_file.writelines(combined_data)

def main(sc_mass, num_jobs, mission_id):
    setup_environment(mission_id, str(sc_mass), RES_DIR, HOME_DIR)
    
    output_dir, param_dir = generate_directory_structure(SCRATCH_DIR, mission_id)
    
    # Clear existing files in the output directory
    clear_directory(output_dir)

    param_file_template = os.path.join(RES_DIR, "parameters_template.txt")
    generate_parameter_files(param_file_template, os.path.join(param_dir, "params"), num_files=num_jobs)

    # Submit jobs to the job scheduler
    spacecraft_model_file = os.path.join(HOME_DIR, mission_id, f"{mission_id}.txt")
    submit_jobs(SRP_TRR_CLASSIC_PATH, param_dir, spacecraft_model_file, output_dir, total_jobs=num_jobs)
    
    # Wait for all jobs to complete
    wait_for_jobs_to_complete()

    # Post-job checks and file combining
    check_log_path = os.path.join(HOME_DIR, mission_id, 'legion_check_log.txt')  # Full path for the log file
    combined_output_path = os.path.join(output_dir, 'combined_output.txt')  # Full path for combined output

    legion_check(output_dir, num_jobs, check_log_path)
    legion_combine(output_dir, combined_output_path, num_jobs)

if __name__ == "__main__":
    # Get the mass, number of jobs, and mission ID from the user
    sc_mass = input("Enter the mass of the spacecraft: ")
    num_jobs = input("Enter the number of jobs: ")
    mission_id = input("Enter the mission ID: ")

    # Convert num_jobs to integer
    num_jobs = int(num_jobs)

    # Run the main function with the provided values
    main(sc_mass, num_jobs, mission_id)
    



