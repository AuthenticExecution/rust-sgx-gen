import os
from .runner import Runner

DEFAULT_LOG_LEVEL = "info"
STUBS_FOLDER = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "stubs")


# Actual crates/modules
# to be checked before adding, because it could be already present
RUST_LAZY = "#[macro_use] extern crate lazy_static;\n"
RUST_INSERT_INPUT = "\t\tm.insert({id}, crate::{name} as fn(&[u8]));\n"
RUST_INSERT_ENTRY = "\t\tm.insert({id}, crate::{name} as fn(&[u8]) -> ResultMessage);\n"
RUST_INSERT_HANDLER = "\t\tm.insert({id}, crate::{name} as fn(&[u8]) -> Vec<u8>);\n"


# Stubs
STUB_MODS_USES = "mods_uses.rs"
STUB_OUTPUT = "output.rs"
STUB_REQUEST = "request.rs"
STUB_CONSTANTS = "constants.rs"
STUB_MAIN = "main.rs"
STUB_AUTH_EXEC = "__authentic_execution.rs"
CARGO_DEPENDENCIES = "common_deps.toml"

DEFAULT_RUNNER = Runner.SGX
STUB_RUNNER_RUN = "__run.rs"
STUB_RUNNER_DEPS = "dependencies.toml"

KEY_LENGTH = 16


# Starting entrypoint index
# 0 is set_key, 1 is attest, 2 is handle_input, 3 is handle_handler
START_ENTRY_INDEX = 4
# Starting indexes of inputs, outputs, requests and handlers
# They need to have different indexes, because the `index` field in Connection does
# not distinguish between them. If the same index is used for different types, bad
# things can happen. Moreover, having these "ranges" allow us do identify what is
# an index: e.g., 25848 is an output, 44 is an input, etc.
# We believe 16384 values for each type is more than enough for a single module.
START_INPUT_INDEX = 0
START_OUTPUT_INDEX = 16384
START_REQUEST_INDEX = 32768
START_HANDLER_INDEX = 49152


# Regex
# Note: [ \t] means space or tab. I use this when I don't explicitly allow newlines
#   (e.g., in comments). \s means any space char (also newlines).
#   This is for non-comment lines
REGEX_LAZY = "^\s*#\s*[\s*macro_use\s*]\s*extern\s*crate\s*lazy_static\s*;"

REGEX_OUTPUT = ("^[ \t]*//@[ \t]*sm_output[ \t]*\([ \t]*"
                "(?P<fname>_?[a-zA-Z]+[_a-zA-Z0-9]*)[ \t]*\)[ \t]*$")

REGEX_INPUT = ("^[ \t]*//@[ \t]*sm_input[ \t]*\n\s*pub\s+fn\s+"
               "(?P<fname>_?[a-zA-Z]+[_a-zA-Z0-9]*)\s*\(\s*_?"
               "[a-zA-Z]+[_a-zA-Z0-9]*\s*:\s*&\s*\[\s*u8\s*]\s*\)\s*\{")

REGEX_ENTRY = ("^[ \t]*//@[ \t]*sm_entry[ \t]*\n\s*pub\s+fn\s+"
               "(?P<fname>_?[a-zA-Z]+[_a-zA-Z0-9]*)\s*\(\s*_?"
               "[a-zA-Z]+[_a-zA-Z0-9]*\s*:\s*&\s*\[\s*u8\s*]\s*\)\s*->\s*"
               "ResultMessage\s*\{")

REGEX_REQUEST = ("^[ \t]*//@[ \t]*sm_request[ \t]*\([ \t]*(?P<fname>_?[a-zA-Z]+"
                 "[_a-zA-Z0-9]*)[ \t]*\)[ \t]*$")

REGEX_HANDLER = ("^[ \t]*//@[ \t]*sm_handler[ \t]*\n\s*pub\s+fn\s+"
                 "(?P<fname>_?[a-zA-Z]+[_a-zA-Z0-9]*)\s*\(\s*_?[a-zA-Z]+"
                 "[_a-zA-Z0-9]*\s*:\s*&\s*\[\s*u8\s*]\s*\)\s*->\s*"
                 "Vec\s*<\s*u8\s*>\s*\{")
