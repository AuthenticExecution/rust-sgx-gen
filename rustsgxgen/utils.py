import os
import logging
import re
import subprocess
import json
from distutils import dir_util
import toml

from . import conf


class Error(Exception):
    pass


def _prepare_output_dir(input_d, output_d):
    dir_util.copy_tree(input_d, output_d)


def _check_input_module(path):
    src = os.path.join(path, "src")
    main = os.path.join(src, "main.rs")
    lib = os.path.join(src, "lib.rs")
    cargo = os.path.join(path, "Cargo.toml")

    # Check if the path is a valid Cargo project
    retval = subprocess.call(["cargo", "verify-project", "--manifest-path", cargo],
                             stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'))

    if retval != 0:
        raise Error("The input path is not a valid Cargo project!")

    # Check absence of main.rs
    if os.path.exists(main):
        raise Error("main.rs file must not exist! Check the rules")

    # Check presence of lib.rs
    if not os.path.exists(lib):
        raise Error("lib.rs file does not exist")

    # Check Cargo.toml structure and dependencies
    cargo = toml.load(cargo)
    if "lib" in cargo:
        raise Error("The Cargo.toml file must not contain a [lib] section!")
    if "bin" in cargo:
        raise Error("The Cargo.toml file must not contain a [[bin]] section!")

    return cargo


def _parse_annotations(file):
    # logging.debug(annotation_file)

    with open(file, "r") as f:
        content = f.read()

    data = {}

    data["inputs"] = __parse_inputs(content)
    content, data["outputs"] = __parse_outputs(content)
    data["entrypoints"] = __parse_entrypoints(content)
    data["handlers"] = __parse_handlers(content)
    content, data["requests"] = __parse_requests(content)

    return content, data


def __parse_inputs(content):
    return __parse(content, conf.REGEX_INPUT, conf.START_INPUT_INDEX)


def __parse_outputs(content):
    return __parse_inject(content, conf.STUB_OUTPUT, conf.REGEX_OUTPUT, conf.START_OUTPUT_INDEX)


def __parse_entrypoints(content):
    return __parse(content, conf.REGEX_ENTRY, conf.START_ENTRY_INDEX)


def __parse_handlers(content):
    return __parse(content, conf.REGEX_HANDLER, conf.START_HANDLER_INDEX)


def __parse_requests(content):
    return __parse_inject(content, conf.STUB_REQUEST, conf.REGEX_REQUEST, conf.START_REQUEST_INDEX)


def __parse(content, regex, start_index):
    p = re.compile(regex, re.MULTILINE | re.ASCII)
    results = p.findall(content)

    return {v: i for (i, v) in enumerate(results, start_index)}


def __parse_inject(content, stub, regex, start_index):
    res_dict = {}
    i = 0
    cnt = 0

    # read stub from file
    with open(os.path.join(conf.STUBS_FOLDER, stub), "r") as f:
        fn = f.read()

    p = re.compile(regex, re.MULTILINE | re.ASCII)
    results = p.finditer(content)

    for result in results:
        res_id = start_index + i
        fname = result.group(1)
        end = result.end()
        #logging.debug("fname: {} end: {}".format(fname, end))
        pos = end + cnt
        inj_fn = fn.format(name=fname, id=res_id)

        content = content[:pos] + inj_fn + content[pos:]
        cnt += len(inj_fn)

        res_dict[fname] = res_id
        i += 1

    return content, res_dict


def _write_module_info(file, name, module_id, data, key=None):
    if key is not None:
        module_info = __helper_write_indexes(
            [(name, "name"), (module_id, "id"), (key, "key")])
    else:
        module_info = __helper_write_indexes(
            [(name, "name"), (module_id, "id")])

    content = {**module_info, **data}

    with open(file, 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=4)


def __helper_write_indexes(data):
    section = {}

    for ind, value in data:
        section[value] = ind

    return section


def _copy_main(src, cargo):
    with open(os.path.join(conf.STUBS_FOLDER, conf.STUB_MAIN), "r") as f:
        content = f.read()

    content = content.format(cargo["package"]["name"])

    with open(os.path.join(src, conf.STUB_MAIN), "w") as f:
        f.write(content)


def _add_fields(dest, src):
    for section in src.keys():
        if section not in dest:
            dest[section] = {}

        for key in src[section].keys():
            if key in dest[section]:
                logging.warning(
                    "{} {} already in destination cargo file, overwriting".format(section, key))

            dest[section][key] = src[section][key]


def _generate_key(length=conf.KEY_LENGTH):
    return os.urandom(length)
