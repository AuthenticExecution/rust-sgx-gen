import os

DEFAULT_LOG_LEVEL = "info"
STUBS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stubs")
LIB_FILE = "lib.rs"
DEFAULT_INFO_FILE = "__sm_info.json"


# Actual crates/modules
RUST_LAZY = "#[macro_use] extern crate lazy_static;\n" # to be checked before adding, because it could be already present
RUST_INSERT_INPUT = "\t\tm.insert({id}, crate::{name} as fn(&[u8]));\n"
RUST_INSERT_ENTRY = "\t\tm.insert({id}, crate::{name} as fn(&[u8]) -> ResultMessage);\n"


# Stubs
STUB_MODS_USES = "mods_uses.rs"
STUB_OUTPUT = "output.rs"
STUB_CONSTANTS = "constants.rs"
STUB_MAIN = "main.rs"
STUB_AUTH_EXEC = "__authentic_execution.rs"
CARGO_DEPENDENCIES = "common_deps.toml"
# runner to load (select the one you want)
DEFAULT_RUNNER = "runner_sgx"
STUB_RUNNER_RUN = "__run.rs"
STUB_RUNNER_DEPS = "dependencies.toml"


# Starting entrypoint index: 0 is set_key, 1 is handle_input
START_ENTRY_INDEX = 2


# Regex
REGEX_LAZY = "^\s*#\s*[\s*macro_use\s*]\s*extern\s*crate\s*lazy_static\s*;"
REGEX_OUTPUT = "^[ \t]*//@[ \t]*sm_output[ \t]*\([ \t]*(?P<fname>_?[a-zA-Z]+[_a-zA-Z0-9]*)[ \t]*\)[ \t]*$"
REGEX_INPUT = "^[ \t]*//@[ \t]*sm_input[ \t]*\n\s*pub\s+fn\s+(?P<fname>_?[a-zA-Z]+[_a-zA-Z0-9]*)\s*\(\s*_?[a-zA-Z]+[_a-zA-Z0-9]*\s*:\s*&\[u8]\s*\)\s*\{"
REGEX_ENTRY = "^[ \t]*//@[ \t]*sm_entry[ \t]*\n\s*pub\s+fn\s+(?P<fname>_?[a-zA-Z]+[_a-zA-Z0-9]*)\s*\(\s*_?[a-zA-Z]+[_a-zA-Z0-9]*\s*:\s*&\[u8]\s*\)\s*->\s*ResultMessage\s*\{"
