import logging
import os
import shutil
import re
import toml
import base64

from . import conf
from .utils import _parse_annotations, _write_module_info, _prepare_output_dir, _check_input_module, _copy_main, _add_fields
from .initialization import _set_parser, _set_logging

def __run(args, cargo):
    out_src = os.path.join(args.output, "src")
    module_name = cargo["package"]["name"]

    ## lib.rs file ##

    lib_file = os.path.join(out_src, conf.LIB_FILE)

    if not os.path.exists(lib_file):
        raise Exception("lib.rs file does not exist")

    # parse annotations, add outputs
    inputs, outputs, entrypoints, content = _parse_annotations(lib_file)
    outputs = { v : i for (i, v) in enumerate(outputs) }
    inputs = { v : i for (i, v) in enumerate(inputs, len(outputs)) }
    entrypoints = { v : i for (i, v) in enumerate(entrypoints, conf.START_ENTRY_INDEX) }

    # read imports
    with open(os.path.join(conf.STUBS_FOLDER, conf.STUB_MODS_USES), "r") as f:
        mods_uses = f.read()

    # search for lazy_static import
    lazy = ""
    if not re.match(conf.REGEX_LAZY, content, re.MULTILINE):
        lazy = conf.RUST_LAZY

    # write new content
    full_str = lazy + "\n" + mods_uses + "\n" + content
    with open(lib_file, "w") as f:
        f.write(full_str)

    ## Authentic Execution file ##

    # read and format constants
    with open(os.path.join(conf.STUBS_FOLDER, conf.STUB_CONSTANTS), "r") as f:
        constants = f.read()

    inputs_fn = ""
    entrypoints_fn = ""
    for input in inputs:
        inputs_fn += conf.RUST_INSERT_INPUT.format(id=inputs[input], name=input)

    for entry in entrypoints:
        entrypoints_fn += conf.RUST_INSERT_ENTRY.format(id=entrypoints[entry], name=entry)

    constants = constants.format(id=args.moduleid, em_port=args.emport, name=module_name, inputs=inputs_fn, entrypoints=entrypoints_fn)

    with open(os.path.join(conf.STUBS_FOLDER, conf.STUB_AUTH_EXEC), "r") as f:
        auth_exec = f.read()

    auth_exec = auth_exec.replace("{CONSTANTS}", constants)

    with open(os.path.join(out_src, conf.STUB_AUTH_EXEC), "w") as f:
        f.write(auth_exec)

    ## Main and other files ##

    _copy_main(out_src, cargo)

    # add runner
    with open(os.path.join(conf.STUBS_FOLDER, args.runner, conf.STUB_RUNNER_RUN), "r") as f:
        runner_file = f.read()

    if args.key:
        runner_file = runner_file.replace("___MODULE_KEY___", base64.b64encode(args.key).decode())
    if args.spkey:
        with open(args.spkey, "r") as f:
            sp_key = f.read()
            runner_file = runner_file.replace("__SP_VKEY_PEM__", sp_key)

    with open(os.path.join(out_src, conf.STUB_RUNNER_RUN), "w") as f:
        f.write(runner_file)

    # edit Cargo.toml adding the dependencies needed
    # general dependencies
    try:
        common_deps = toml.load(os.path.join(conf.STUBS_FOLDER, conf.CARGO_DEPENDENCIES))
        for key in common_deps.keys():
            _add_fields(cargo, common_deps, key)
    except Exception as e:
        logging.error("Common deps file not found")
        raise e

    # runner dependencies
    try:
        runner_deps = toml.load(os.path.join(conf.STUBS_FOLDER, args.runner, conf.STUB_RUNNER_DEPS))
        for key in runner_deps.keys():
            _add_fields(cargo, runner_deps, key)
    except Exception as e:
        logging.warn("Runner dependencies file not found")

    # write to cargo
    with open(os.path.join(args.output, "Cargo.toml"), "w") as f:
        toml.dump(cargo, f)

    # write to an output file module name, inputs, outputs, entrypoints as well as their index
    if args.print:
        _write_module_info(module_name, args, inputs, outputs, entrypoints)

    logging.debug("Done")

    return inputs, outputs, entrypoints


def generate(args):
    try:
        logging.debug("Checking input project..")
        # check if the input dir is a correct Rust Cargo module
        cargo = _check_input_module(args.input)

        logging.debug("Creating output project..")
        # copy dir
        _prepare_output_dir(args.input, args.output)

        logging.debug("Updating code..")
        # execute logic
        return __run(args, cargo)

    except Exception as e:
        logging.error(e)

        if os.path.exists(args.output):
            shutil.rmtree(args.output)

        exit(1)


def __main():
    # argument parser
    parser = _set_parser()
    args = parser.parse_args()

    # set logging params
    _set_logging(args.loglevel)
    generate(args)


if __name__ == "__main__":
    __main()
