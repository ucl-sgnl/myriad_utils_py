import os
import subprocess
import shutil
import time
from multiprocessing import Pool

SCRATCH_DIR = os.path.join("Scratch")
SRP_TRR_CLASSIC_PATH = os.path.join("/Users/charlesc/Documents/GitHub/ucl-sgnl/srp_trr_classic/bin/srp_trr_classic")
RES_DIR = os.path.join("res")

def generate_directory_structure(base_dir, mission):
    output_dir = os.path.join(base_dir, mission, "spiralPoints", "outputFiles")
    param_dir = os.path.join(base_dir, mission, "spiralPoints", "paramFiles")

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(param_dir, exist_ok=True)

    return output_dir, param_dir

def generate_parameter_files(template_filename, output_prefix, num_files, model_type, scheme, spacing, sr_option, emissivity):
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

def setup_environment(mission, mass, res_dir):
    mission_dirs = [
        os.path.join(mission),
        os.path.join(mission, "spiralPoints"),
        os.path.join(mission, "spiralPoints", "paramFiles"),
        os.path.join(mission, "spiralPoints", "outputFiles")
    ]
    for dir_path in mission_dirs:
        os.makedirs(dir_path, exist_ok=True)

    shutil.copy(f"{res_dir}/parameters_template.txt", f"{mission}/parameters.txt")
    with open(f"{mission}/parameters.txt", 'r') as file:
        lines = file.readlines()

    updated_lines = []
    mass_line_found = False
    for line in lines:
        if "// mass of spacecraft (kg)" in line and not mass_line_found:
            updated_lines.append(line)
            mass_line_found = True
        elif mass_line_found:
            updated_lines.append(f"mass         = {mass}\n")
            mass_line_found = False
        else:
            updated_lines.append(line)

    with open(f"{mission}/parameters.txt", 'w') as file:
        file.writelines(updated_lines)

def run_srp_trr_classic(param_file, spacecraft_model_file, output_file):
    subprocess.run([SRP_TRR_CLASSIC_PATH, param_file, spacecraft_model_file, output_file])

def submit_jobs(param_files_dir, spacecraft_model_file, output_files_dir, total_jobs=100):
    param_files = [os.path.join(param_files_dir, f"params{str(i).zfill(5)}.txt") for i in range(1, total_jobs + 1)]
    output_files = [os.path.join(output_files_dir, f"output{str(i).zfill(5)}.txt") for i in range(1, total_jobs + 1)]
    jobs = [(param_files[i], spacecraft_model_file, output_files[i]) for i in range(total_jobs)]

    with Pool(processes=os.cpu_count()) as pool:
        pool.starmap(run_srp_trr_classic, jobs)

def legion_check(output_dir, expected_files, logfile=None):
    missing_files = []
    line_count_issues = []

    for i in range(1, expected_files + 1):
        file_name = f"output{str(i).zfill(len(str(expected_files)))}.txt"
        file_path = os.path.join(output_dir, file_name)
        if not os.path.exists(file_path):
            missing_files.append(file_name)
        else:
            with open(file_path, 'r') as file:
                lines = file.readlines()
                if len(lines) != 2:
                    line_count_issues.append((file_name, len(lines)))

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
    combined_data = []

    for i in range(1, expected_files + 1):
        file_name = f"output{str(i).zfill(5)}.txt"
        file_path = os.path.join(output_dir, file_name)
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                lines = file.readlines()[1:]
                combined_data.extend(lines)
        else:
            print(f"Warning: File {file_path} not found.")

    try:
        combined_data.sort(key=lambda x: float(x.split(',')[0]))
    except ValueError:
        print("Warning: Unable to sort combined data numerically. Data will be combined as is.")

    with open(combined_output_file, 'w') as output_file:
        output_file.write("Sun_lat,Sun_lon,acc_X,acc_Y,acc_Z,EPS_angle\n")
        output_file.writelines(combined_data)

def main(mission_id, mode, sc_mass=None, num_jobs=None, model_type=None, scheme=None, spacing=None, sr_option=None, emissivity=None):
    if mode == "submit":
        setup_environment(mission_id, str(sc_mass), RES_DIR)
        output_dir, param_dir = generate_directory_structure(SCRATCH_DIR, mission_id)
        param_file_template = os.path.join(RES_DIR, "parameters_template.txt")
        generate_parameter_files(param_file_template, os.path.join(param_dir, "params"), num_jobs, model_type, scheme, spacing, sr_option, emissivity)
        spacecraft_model_file = os.path.join(mission_id, f"{mission_id}.txt")
        submit_jobs(param_dir, spacecraft_model_file, output_dir, total_jobs=num_jobs)
        print("Jobs submitted.")
    elif mode == "check" or mode == "combine":
        output_dir = os.path.join(SCRATCH_DIR, mission_id, "spiralPoints", "outputFiles")
        if mode == "check":
            check_log_path = os.path.join(mission_id, 'legion_check_log.txt')
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
        scheme = input("Enter the pixel array orientation scheme (0 for EPS angles, 1 for spiral points, 2 for AzEl): ")
        spacing = input("Enter the pixel spacing of array (m): ")
        sr_option = input("Include secondary reflections? (Y or N): ")
        emissivity = input("Enter the MLI emissivity for TRR models: ")
        main(mission_id, mode, sc_mass, num_jobs, model_type, scheme, spacing, sr_option, emissivity)
    else:
        num_jobs = int(input("Enter the number of jobs to check/combine: "))
        main(mission_id, mode, num_jobs=num_jobs)
