import os
import fnmatch
import sys
import re
from copy import copy
from urllib.request import urlopen

def path_exists(uri_str, is_dir=False):
    if is_dir:
        return os.path.isdir(uri_str)
    else:
        return os.path.isfile(uri_str)

def remote_uri_exists(uri_str):
    try:
        _ = urlopen(uri_str)
        return True
    except:
        return False

def search_file_or_dir(glob_pattern, is_dir=False, input_dir="", search_subdirs=True):
    if not '*' in glob_pattern:
        glob_pattern = "*" + glob_pattern + "*"
    result = []
    for root, dirs, files in os.walk(input_dir):
        if is_dir:
            objects = dirs
        else:
            objects = files
        for name in objects:
            if fnmatch.fnmatch(name, glob_pattern):
                result.append(os.path.join(root, name))
    assert len(result) <= 1, (
        "multiple hits when searching for file or dir with glob_pattern \"" + glob_pattern + "\": " + 
        ", ".join(result)
    )
    assert len(result) != 0, "no hits found when searching for file or dir with glob_pattern \"" + glob_pattern + "\""
    return os.path.abspath(result[0])


def get_file_or_dir_uri(uri_str, is_dir=False, search_paths=True, search_subdirs=True, 
    validate_uris=True, allow_remote_uri=True, allow_local_path=True, input_dir=None
):
    if input_dir is None: input_dir_abs = ""
    else: input_dir_abs = os.path.abspath(input_dir)
    if validate_uris:
        if allow_remote_uri and remote_uri_exists(uri_str):
            uri=uri_str
        elif allow_local_path and path_exists(uri_str, is_dir): 
            uri=os.path.abspath(uri_str)
        elif allow_local_path and \
            input_dir is not None and \
            path_exists(os.path.join(input_dir_abs, uri_str), is_dir): 
            uri=os.path.join(input_dir_abs, uri_str)
        elif allow_local_path and \
            input_dir is not None and \
            search_paths:
            try:
                uri=search_file_or_dir(uri_str, is_dir, input_dir, search_subdirs)
            except AssertionError as e:
                raise AssertionError( str(e) )        
        else:
            raise AssertionError( "the path/URI to \"" + uri_str + "\" is not valid")
    else:
        uri=uri_str
    return uri


def class_file(value_string, secondary_files, validate_uris=True, search_paths=True, search_subdirs=True, allow_remote_uri=True, allow_local_path=True, input_dir=None):
    try:
        path = get_file_or_dir_uri(
            uri_str=value_string, 
            is_dir=False, 
            search_paths=search_paths, 
            search_subdirs=search_subdirs,
            validate_uris=validate_uris, 
            allow_remote_uri=allow_remote_uri,
            allow_local_path=allow_local_path,
            input_dir=input_dir
        )
    except AssertionError as e:
        raise AssertionError( str(e) )
    if secondary_files[0] != "":
        for sec_ext in secondary_files:
            if sec_ext[0] == "^":
                capture_sec_ext = re.search('^(\^+)(.*)', sec_ext)
                n_exts_to_rm = len(capture_sec_ext.group(1))
                value_root = copy(path) 
                for idx in range(0,n_exts_to_rm):
                  value_root = os.path.splitext(value_root)[0]
                sec_file_item_path =value_root + capture_sec_ext.group(2)
            else:
                sec_file_item_path = path + sec_ext
            try:
                sec_file_item_path = get_file_or_dir_uri(
                    uri_str=sec_file_item_path, 
                    is_dir=False, 
                    search_paths=False, 
                    search_subdirs=search_subdirs,
                    validate_uris=validate_uris, 
                    allow_remote_uri=allow_remote_uri,
                    allow_local_path=allow_local_path
                )
            except AssertionError as e:
                raise AssertionError("invalid secondary file for \"" + value_string + "\": " + str(e) )
    return path


def class_directory(value_string, validate_uris=True, search_paths=True, search_subdirs=True, allow_remote_uri=True, allow_local_path=True, input_dir=None):
    try:
        path = get_file_or_dir_uri(
            uri_str=value_string, 
            is_dir=True, 
            search_paths=search_paths, 
            search_subdirs=search_subdirs,
            validate_uris=validate_uris, 
            allow_remote_uri=allow_remote_uri,
            allow_local_path=allow_local_path,
            input_dir=input_dir
        )
    except AssertionError as e:
        raise AssertionError( str(e) )
    return path


def boolean(value_string ):
    if value_string in ["true", "True", "TRUE", "T", "t", "Yes", "YES", "yes", "y", "Y", "1"]:
        return True
    elif value_string in ["false", "False", "FALSE", "F", "f", "No", "NO", "no", "n", "N", "0"]:
        return False
    else:
        raise AssertionError( "\"" + value_string + "\" cannot be coerced into boolean")


def match_type( param_name, all_param_values, configs, validate_uris=True, search_paths=True, search_subdirs=True, allow_remote_uri=True, allow_local_path=True, input_dir=""):
    type_matching_functions = { 
        "boolean":boolean,
        "int":int,
        "string":str,
        "long":int, # currently there is a problem with printing long in python2
        "float":float,
        "double":float
    }
    value = all_param_values[param_name]
    # check if non-array paramaeters have at 1 field:
    assert not ( not configs[param_name]["is_array"] and len(value) > 1), "parameter is no array but has more than one value."
    # check if value containes not allowed null entries:
    assert not ((value[0] == "null" or value[0] == "") and 
        not configs[param_name]["null_allowed"]
    ), "parameter is \"null\" but this is not allowed."
    assert not (
        not configs[param_name]["is_array"] and 
        (value[0] == "itemNull")
    ), "Parameter is set to \"itemNull\" but it is not an array/list."
    assert not (
        (value[0] == "itemNull") and 
        not configs[param_name]["null_items_allowed"]
    ), "The list parameter contains \"itemNull\", however, null items are not allowed."
    
    # check if parameter contains empty values:
    assert not "" in value, "empty string detected \"\"."
    # check and translate each entry of value into the desired type:
    value_type_matched = []
    for value_string in value:
        try:
            if value_string in ["null", "itemNull"]:
                value_type_matched.append( None )
            else:
                if configs[param_name]["type"] == "File":
                    value_type_matched.append( 
                        class_file(
                            value_string=value_string,
                            secondary_files=configs[param_name]["secondary_files"], 
                            validate_uris=validate_uris, 
                            search_paths=search_paths, 
                            search_subdirs=search_subdirs,
                            allow_remote_uri=allow_remote_uri, 
                            allow_local_path=allow_local_path, 
                            input_dir=input_dir
                        ) 
                    )
                elif configs[param_name]["type"] == "Directory":
                    value_type_matched.append( 
                        class_directory(
                            value_string=value_string,
                            validate_uris=validate_uris, 
                            search_paths=search_paths, 
                            search_subdirs=search_subdirs,
                            allow_remote_uri=allow_remote_uri, 
                            allow_local_path=allow_local_path, 
                            input_dir=input_dir
                        ) 
                    )
                else:
                    value_type_matched.append( type_matching_functions[configs[param_name]["type"]](value_string) )
        except Exception as e:
            raise AssertionError( "value \"" + value_string + "\" is not compatible with allowed type " + configs[param_name]["type"] + ": " + str(e))
    if not configs[param_name]["is_array"]:
        value_type_matched = value_type_matched[0]
    return value_type_matched

def get_type_matched_param_values( param_values, configs, validate_uris=True, search_paths=True, search_subdirs=True, allow_remote_uri=True, allow_local_path=True, input_dir=""):
    print_pref = "[match_all_param_types]:"
    param_values_type_matched = {}
    for param_name in param_values.keys():
        param_value = param_values[param_name]
        if configs[param_name]["type"] == "helper":
            continue
        if len(param_value) == 0 or (len(param_values[param_name]) == 1 and param_value[0] == ""):
            if configs[param_name]["null_allowed"]:
                param_values_type_matched[param_name] = None
                continue
            else:
                raise AssertionError( print_pref + " parameter \"" + param_name + "\" failes type matching: " + 
                    "parameter was empty but null is not allowed.")
        try:
            param_values_type_matched[param_name] = match_type(param_name, param_values, configs,
                validate_uris, search_paths, search_subdirs, allow_remote_uri, allow_local_path, input_dir)
        except AssertionError as e:
            raise AssertionError( print_pref + " parameter \"" + param_name + "\" failes type matching: " + str(e) )
    return param_values_type_matched