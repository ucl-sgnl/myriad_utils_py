import os
import subprocess
import shutil
import time
# Constants

SCRATCH_DIR = "Scratch"
SRP_TRR_CLASSIC_PATH = "/home/zcesccc/srp_trr_classic/bin/srp_trr_classic"
RES_DIR = "res"
HOME_DIR = "."

def wait_for_jobs_to_complete():
    """Waits for all submitted jobs to complete before proceeding."""
    print("Waiting for jobs to complete...")
    jobs_running = True
    while jobs_running:
        time.sleep(30)  # Check every 30sec
        result = subprocess.run(["qstat"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
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

def generate_parameter_files(template_filename, output_prefix, num_files, model_type, scheme, spacing, sr_option, emissivity):
    """
    Generates parameter files based on a template with user-defined settings.

    :param template_filename: Path to the template file.
    :param output_prefix: Prefix for the output files.
    :param num_files: Number of parameter files to generate.
    :param model_type: Type of modeling required (0 for SRP, 1 for SRP+TRR, 2 for TRR).
    :param scheme: Pixel array orientation scheme (0 for EPS angles, 1 for spiral points).
    :param spacing: Pixel spacing of the array.
    :param sr_option: Option to include secondary reflections (Y or N).
    :param emissivity: MLI emissivity for TRR models.
    """
    with open(template_filename, 'r') as template_file:
        template_content = template_file.readlines()

    for file_index in range(1, num_files + 1):
        output_filename = f"{output_prefix}{str(file_index).zfill(5)}.txt"
        with open(output_filename, 'w') as output_file:
            for line in template_content:
                if line.strip().startswith("model_type"):
                    output_file.write(f"model_type   = {model_type}\n")
                elif line.strip().startswith("scheme"):
                    output_file.write(f"scheme       = {scheme}\n")
                elif line.strip().startswith("spacing"):
                    output_file.write(f"spacing      = {spacing}\n")
                elif line.strip().startswith("sr_option"):
                    output_file.write(f"sr_option    = {sr_option}\n")
                elif line.strip().startswith("emissivity"):
                    output_file.write(f"emissivity   = {emissivity}\n")
                elif line.strip().startswith("k_start"):
                    output_file.write(f"k_start      = {file_index}\n")
                elif line.strip().startswith("k_finish"):
                    output_file.write(f"k_finish     = {file_index}\n")
                elif line.strip().startswith("n_points"):
                    output_file.write(f"n_points     = {num_files}\n")
                else:
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
        # [Previous directory setup code remains unchanged]
    ]
    for dir_path in mission_dirs:
        os.makedirs(dir_path, exist_ok=True)

    # Copy parameter file and update spacecraft mass
    shutil.copy(f"{res_dir}/parameters_template.txt", f"{home_dir}/{mission}/parameters.txt")
    with open(f"{home_dir}/{mission}/parameters.txt", 'r') as file:
        lines = file.readlines()

    updated_lines = []
    mass_line_found = False
    for line in lines:
        if "// mass of spacecraft (kg)" in line and not mass_line_found:
            updated_lines.append(line)  # Keep the comment line
            mass_line_found = True  # Flag to indicate the mass line is next
        elif mass_line_found:
            updated_lines.append(f"mass         = {mass}\n")  # Update the mass value
            mass_line_found = False  # Reset the flag
        else:
            updated_lines.append(line)  # Keep all other lines as they are

    with open(f"{home_dir}/{mission}/parameters.txt", 'w') as file:
        file.writelines(updated_lines)

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
    Submits a job array to the job scheduler, ensuring correct argument passing.
    """
    job_script_filename = "job_array_script.sh"
    
    # Ensure absolute paths are used for directories and files
    absolute_output_files_dir = os.path.abspath(output_files_dir)
    absolute_param_files_dir = os.path.abspath(param_files_dir)
    absolute_spacecraft_model_file = os.path.abspath(spacecraft_model_file)

    with open(job_script_filename, "w") as file:
        file.writelines([
            "#!/bin/bash -l\n",
            "#$ -S /bin/bash\n",
            "#$ -l h_rt=5:00:0\n",
            "#$ -l mem=512M\n",
            f"#$ -t 1-{total_jobs}\n",
            "#$ -N srp_trr_job_array\n",
            f"#$ -wd {absolute_output_files_dir}\n\n",
            "module unload mkl/10.2.5/035\n",
            "module unload mpi/qlogic/1.2.7/intel\n",
            "module unload compilers/intel/11.1/072\n",
            "module load compilers/gnu/4.1.2\n",
            "module load mpi/qlogic/1.2.7/gnu\n\n",
            f"param_file={absolute_param_files_dir}/params$(printf '%05d' $SGE_TASK_ID).txt\n",
            f"output_file={absolute_output_files_dir}/output$(printf '%05d' $SGE_TASK_ID).txt\n\n",
            f"{srp_trr_classic_path} $param_file {absolute_spacecraft_model_file} $output_file\n"
        ])

    subprocess.run(["qsub", job_script_filename])

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

    # Summary with clearer success message
    if not missing_files and not line_count_issues:
        success_message = "All checks passed successfully. No missing files, no repeated spiral points, and no error entries found."
        print(success_message)
        if logfile:
            with open(logfile, 'a') as log_file:
                log_file.write('\n' + success_message)
    else:
        summary = "There is a problem with one or more output files."
        print(summary)
        if logfile:
            with open(logfile, 'a') as log_file:
                log_file.write('\n' + summary)

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
        file_name = f"output{str(i).zfill(5)}.txt"
        file_path = os.path.join(output_dir, file_name)
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                lines = file.readlines()[1:]  # Skip header line
                combined_data.extend(lines)
        else:
            print(f"Warning: File {file_path} not found.")

    # Attempt to sort combined data based on the first column (if it's numeric)
    try:
        combined_data.sort(key=lambda x: float(x.split(',')[0]))
    except ValueError:
        print("Warning: Unable to sort combined data numerically. Data will be combined as is.")

    # Write combined data to a file
    with open(combined_output_file, 'w') as output_file:
        output_file.write("Sun_lat,Sun_lon,acc_X,acc_Y,acc_Z,EPS_angle\n")  # Adding header
        output_file.writelines(combined_data)

def main(sc_mass, num_jobs, mission_id, model_type, scheme, spacing, sr_option, emissivity):
    setup_environment(mission_id, str(sc_mass), RES_DIR, HOME_DIR)
    
    output_dir, param_dir = generate_directory_structure(SCRATCH_DIR, mission_id)

    param_file_template = os.path.join(RES_DIR, "parameters_template.txt")
    generate_parameter_files(param_file_template, os.path.join(param_dir, "params"), num_jobs, model_type, scheme, spacing, sr_option, emissivity)

    spacecraft_model_file = os.path.join(HOME_DIR, mission_id, f"{mission_id}.txt")
    submit_jobs(SRP_TRR_CLASSIC_PATH, param_dir, spacecraft_model_file, output_dir, total_jobs=num_jobs)
    
    wait_for_jobs_to_complete()

    check_log_path = os.path.join(HOME_DIR, mission_id, 'legion_check_log.txt')
    combined_output_path = os.path.join(output_dir, 'combined_output.txt')

    legion_check(output_dir, num_jobs, check_log_path)
    legion_combine(output_dir, combined_output_path, num_jobs)

def main(mission_id, mode, sc_mass=None, num_jobs=None, model_type=None, scheme=None, spacing=None, sr_option=None, emissivity=None):
    if mode == "submit":
        setup_environment(mission_id, str(sc_mass), RES_DIR, HOME_DIR)
        output_dir, param_dir = generate_directory_structure(SCRATCH_DIR, mission_id)
        param_file_template = os.path.join(RES_DIR, "parameters_template.txt")
        generate_parameter_files(param_file_template, os.path.join(param_dir, "params"), num_jobs, model_type, scheme, spacing, sr_option, emissivity)
        spacecraft_model_file = os.path.join(HOME_DIR, mission_id, f"{mission_id}.txt")
        submit_jobs(SRP_TRR_CLASSIC_PATH, param_dir, spacecraft_model_file, output_dir, total_jobs=num_jobs)
        print("Jobs submitted. You can check the job status using 'qstat'.")
    elif mode == "check" or mode == "combine":
        output_dir = os.path.join(SCRATCH_DIR, mission_id, "spiralPoints", "outputFiles")
        if mode == "check":
            check_log_path = os.path.join(HOME_DIR, mission_id, 'legion_check_log.txt')
            legion_check(output_dir, num_jobs, check_log_path)
        elif mode == "combine":
            combined_output_path = os.path.join(output_dir, 'combined_output.txt')
            legion_combine(output_dir, combined_output_path, num_jobs)

if __name__ == "__main__":
    mission_id = input("Enter the mission ID: ")
    mode = input("Enter mode (submit/check/combine): ")

    if mode == "submit":
        sc_mass = input("Enter the mass of the spacecraft: ")
        num_jobs = int(input("Enter the number of jobs: "))
        model_type = input("Enter the type of modelling required (0 for SRP, 1 for SRP+TRR, 2 for TRR): ")
        scheme = input("Enter the pixel array orientation scheme (0 for EPS angles, 1 for spiral points): ")
        spacing = input("Enter the pixel spacing of array (m): ")
        sr_option = input("Include secondary reflections? (Y or N): ")
        emissivity = input("Enter the MLI emissivity for TRR models: ")
        main(mission_id, mode, sc_mass, num_jobs, model_type, scheme, spacing, sr_option, emissivity)
    else:
        num_jobs = int(input("Enter the number of jobs to check/combine: "))
        main(mission_id, mode, num_jobs=num_jobs)