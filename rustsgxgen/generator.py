import logging
import os
import sys
import re
import base64
import toml

from . import conf
from .utils import _parse_annotations, _write_module_info, _prepare_output_dir, \
    _check_input_module, _copy_main, _add_fields, \
    _generate_key
from .initialization import _set_parser, _set_logging


def __run(args, cargo):
    out_src = os.path.join(args.output, "src")
    module_name = cargo["package"]["name"]

    ## lib.rs file ##
    # In this section, we update lib.rs:
    # - parse the annotations (inputs, outputs, entry points)
    # - add imports (for authentic execution functions and constants)

    lib_file = os.path.join(out_src, "lib.rs")

    # parse annotations
    content, data = _parse_annotations(lib_file)

    # read imports
    with open(os.path.join(conf.STUBS_FOLDER, conf.STUB_MODS_USES), "r") as f:
        mods_uses = f.read()

    # search for lazy_static import (if already present, we do not add it again)
    lazy = ""
    if not re.match(conf.REGEX_LAZY, content, re.MULTILINE):
        lazy = conf.RUST_LAZY

    # write new content
    complete_lib = lazy + "\n" + mods_uses + "\n" + content
    with open(lib_file, "w") as f:
        f.write(complete_lib)

    ## Authentic Execution file ##
    # In this section, we add to the project all the needed for authentic execution
    # we also need to update some data structures with the information retrieved
    # before

    with open(os.path.join(conf.STUBS_FOLDER, conf.STUB_CONSTANTS), "r") as f:
        constants = f.read()

    # add inputs entrypoints, handlers functions to hashmaps, so that they can
    # be called given their ID
    inputs = data["inputs"]
    inputs_fn = ""
    for _input in inputs:
        inputs_fn += conf.RUST_INSERT_INPUT.format(
            id=inputs[_input], name=_input)

    entrypoints = data["entrypoints"]
    entrypoints_fn = ""
    for entry in entrypoints:
        entrypoints_fn += conf.RUST_INSERT_ENTRY.format(
            id=entrypoints[entry], name=entry)

    handlers = data["handlers"]
    handlers_fn = ""
    for handler in handlers:
        handlers_fn += conf.RUST_INSERT_HANDLER.format(
            id=handlers[handler], name=handler)

    # format constants with module's info
    constants = constants.format(id=args.moduleid, em_port=args.emport,
                                 name=module_name, inputs=inputs_fn,
                                 entrypoints=entrypoints_fn, handlers=handlers_fn)

    # add constants to authentic_execution file, add the file to project
    with open(os.path.join(conf.STUBS_FOLDER, conf.STUB_AUTH_EXEC), "r") as f:
        auth_exec = f.read()

    auth_exec = auth_exec.replace("{CONSTANTS}", constants)

    with open(os.path.join(out_src, conf.STUB_AUTH_EXEC), "w") as f:
        f.write(auth_exec)

    ## Main and other files ##
    # Here, we will add the logic for main(): the project will not be a Cargo lib
    # anymore, but an executable

    _copy_main(out_src, cargo)

    # add runner
    # sgx: the master key is retrieved by means of Remote Attestation (RA)
    # native: the master key is generated here and hardcoded inside the code
    runner = args.runner
    runner_folder = os.path.join(conf.STUBS_FOLDER, runner.to_str())

    # add __run.rs, that includes the main logic and the logic for the key
    with open(os.path.join(runner_folder, conf.STUB_RUNNER_RUN), "r") as f:
        runner_file = f.read()

    if runner.has_hardcoded_key():
        # key is hardcoded
        master_key = _generate_key()
        encoded_key = base64.b64encode(master_key).decode()
        runner_file = runner_file.replace("___MODULE_KEY___", encoded_key)
    else:
        # key is retrieved through remote attestation
        master_key = None
        encoded_key = None
        if args.spkey:
            with open(args.spkey, "r") as f:
                sp_key = f.read() + "\\0"
                runner_file = runner_file.replace("__SP_VKEY_PEM__", sp_key)
        else:
            logging.warning(
                "ra_sp public key not provided as input! RA won't work")

    with open(os.path.join(out_src, conf.STUB_RUNNER_RUN), "w") as f:
        f.write(runner_file)

    ## Finally, edit Cargo.toml adding the needed dependencies ##

    # general dependencies (common to all runners)
    try:
        common_deps = toml.load(os.path.join(
            conf.STUBS_FOLDER, conf.CARGO_DEPENDENCIES))
        _add_fields(cargo, common_deps)
    except Exception as e:
        logging.error("Common deps file not found")
        raise e

    # runner dependencies
    try:
        runner_deps = toml.load(os.path.join(
            runner_folder, conf.STUB_RUNNER_DEPS))
        _add_fields(cargo, runner_deps)
    except Exception as e:
        logging.warning("Runner dependencies file not found")

    # write to cargo
    with open(os.path.join(args.output, "Cargo.toml"), "w") as f:
        toml.dump(cargo, f)

    # write module info to output file (if specified)
    if args.print:
        _write_module_info(args.print, module_name,
                           args.moduleid, data, encoded_key)

    logging.debug("Done")

    return data, master_key


def generate(args):
    try:
        # check if the input dir is a correct Rust Cargo module
        logging.debug("Checking input project..")
        cargo = _check_input_module(args.input)

        # copy dir
        logging.debug("Creating output project..")
        _prepare_output_dir(args.input, args.output)

        # generate code
        logging.debug("Generating code..")
        return __run(args, cargo)

    except Exception as e:
        logging.error(e)
        sys.exit(1)


def __main():
    # argument parser
    parser = _set_parser()
    args = parser.parse_args()

    # set logging params
    _set_logging(args.loglevel)
    generate(args)


if __name__ == "__main__":
    __main()
