import shutil
import os
import logging
import toml
import re
import subprocess
import json
import base64

from . import conf


def _prepare_output_dir(input, output):
    if not os.path.exists(output):
        os.mkdir(output)
    shutil.copytree(os.path.join(input, "src"), os.path.join(output, "src"))
    shutil.copy(os.path.join(input, "Cargo.toml"), os.path.join(output, "Cargo.toml"))


def _check_input_module(path):
    src = os.path.join(path, "src")
    main = os.path.join(src, "main.rs")
    cargo = os.path.join(path, "Cargo.toml")

    # Check if the path is a valid Cargo project
    retval = subprocess.call(["cargo",  "verify-project", "--manifest-path", cargo], stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'))

    if retval != 0:
        raise Exception("The input path is not a valid Cargo project!")

    # Check absence of main.rs
    if os.path.exists(main):
        raise Exception("The main.rs file must not exist! Check the rules")

    # Check Cargo.toml structure and dependencies
    cargo = toml.load(cargo)
    if "lib" in cargo:
        raise Exception("The Cargo.toml file must not contain a [lib] section!")
    if "bin" in cargo:
        raise Exception("The Cargo.toml file must not contain a [[bin]] section!")

    return cargo


def _parse_annotations(file):
    #logging.debug(annotation_file)

    with open(file, "r") as f:
        content = f.read()

    new_content, outputs = __parse_outputs(content)
    inputs = __parse_inputs(content)
    entrypoints = __parse_entrypoints(content)

    return inputs, outputs, entrypoints, new_content


def __parse_outputs(content):
    outputs = []
    id = 0
    cnt = 0

    # read output stub from file
    with open(os.path.join(conf.STUBS_FOLDER, conf.STUB_OUTPUT), "r") as f:
        fn = f.read()

    p = re.compile(conf.REGEX_OUTPUT, re.MULTILINE | re.ASCII)
    results = p.finditer(content)

    for result in results:
        fname = result.group(1)
        end = result.end()
        #logging.debug("fname: {} end: {}".format(fname, end))
        pos = end + cnt
        inj_fn = fn.format(name=fname, id=id)

        content = content[:pos] + inj_fn + content[pos:]
        cnt += len(inj_fn)

        id += 1
        outputs.append(fname)

    return content, outputs


def __parse_inputs(content):
    return __parse_input_entry(content, conf.REGEX_INPUT)


def __parse_entrypoints(content):
    return __parse_input_entry(content, conf.REGEX_ENTRY)


def __parse_input_entry(content, regex):
    vals = []

    p = re.compile(regex, re.MULTILINE | re.ASCII)
    results = p.findall(content)

    return results


def _write_module_info(package, args, inputs, outputs, entrypoints):
    file = args.print

    if args.key:
        content = __helper_write_indexes([(package, "name"), (args.moduleid, "id"), (base64.b64encode(args.key).decode(), "key")])
    else:
        content = __helper_write_indexes([(package, "name"), (args.moduleid, "id")])

    content["inputs"] = inputs
    content["outputs"] = outputs
    content["entrypoints"] = entrypoints

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


def _add_fields(dest, src, section):
    if section not in src:
        logging.debug("{} not present in source file".format(section))
        return

    if section not in dest:
        dest[section] = {}

    for key in src[section].keys():
        if key in dest[section]:
            logging.warn("{} {} already in destination cargo file, overwriting".format(section, key))

        dest[section][key] = src[section][key]
