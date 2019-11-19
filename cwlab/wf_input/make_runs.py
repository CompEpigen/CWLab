import yaml
import os
import sys

def write_run( type_mached_params, configs, wf_type, output_dir=".", output_basename="" ):
    if output_basename == "":
        output_basename = "run"
    if wf_type == "CWL":
        output = {}
        for param in type_matched_params.keys():
            if configs[param]["type"] in ["File", "Directory"]:
                output[param] = {
                    "class": configs[param]["type"],
                    "path": type_mached_params[param]
                }
                if configs[param]["type"] == "File" and configs[param_name]["secondary_files"][0] != "":
                    cwl_sec_file_array = []
                    for sec_ext in configs[param_name]["secondary_files"]:
                        if sec_ext[0] == "^":
                            capture_sec_ext = re.search('^(\^+)(.*)', sec_ext)
                            n_exts_to_rm = len(capture_sec_ext.group(1))
                            value_root = path 
                            for idx in range(0,n_exts_to_rm):
                                value_root = os.path.splitext(value_root)[0]
                            sec_file_item_path =value_root + capture_sec_ext.group(2)
                        else:
                            sec_file_item_path = path + sec_ext
                        cwl_sec_file_array.append( {"class": "File", "path": sec_file_item_path } )
                    output[param]["secondaryFiles"] = cwl_sec_file_array
            else:
                output[param] = type_mached_params[param]
    else:
        output = type_mached_params
    file_path = os.path.join(output_dir, output_basename + ".yaml")
    with open(file_name, 'w') as outfile:
        yaml.dump(output, outfile)

def write_multiple_runs(type_matched_params_by_run_id, configs, wf_type, output_dir=".", output_basename=""):
    assert os.path.isdir(output_dir), "Output directory \"" + output_dir + "\" does not exist."
    for run_id in type_matched_params_by_run_id.keys():
        write_run(
            type_matched_params_by_run_id[run_id],  
            configs, wf_type, output_dir, output_basename + "_" + run_id
        )