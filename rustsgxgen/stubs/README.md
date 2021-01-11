# Stubs

Stub Rust files to provide standard functions / data structures / macro definitions for software modules

## Stub functions

- `set_key`
  - the content of this function **must** be encrypted with the module's key. How can i easily deal with this?
  - basic initial solution: hardcode the module's key inside the software module. Two options:
    - the developer generates and hardcodes the key by itself (saved in a specific static variable)
    - the key is generated automatically by my scripts and then returned in the result.json file (preferred right now)
  - Then ask for suggestions
- `handle_input`
- `handle_output`
- `handle_entrypoint`
  - calls the requested entry point, gets the return value and sends it to the EM
- `main`
  - the main function will initialize everything, and will wait for messages from the EM

### Return values from functions

- `handle_entrypoint` (and all the entrypoints) returns a `Result<Vec<u8>, Vec<u8>>`
  - Success: a vector with the response

## Data structures / Collections

### Constants

- Module's key: private module's symmetric key. This is known only by the module and the deployer
  - not accessible by the developer
  - **it is defined inside the runner**, each runner has to implement a logic to retrieve the key
    - by running the code injection script with the flag `-k`, a key is automatically generated and hardcoded, if the value of the key is `___MODULE_KEY___`. See runners for more information

- Module ID: a 16-bit module identifier, assigned at compile time by the deployer
  - at the moment, accessible through `*crate::__authentic_execution::authentic_execution::MODULE_ID`

- Module name: a string, used for debugging or other purposes

- EM port: TCP port of the Event Manager, accessible by connecting through the loopback interface

- Inputs: Map <input_index> -> <input_handler>
  - not accessible by the developer

- Entry points: Map <entry_index> -> <entry_handler>
  - not accessible by the developer

### Variables

- `Connection`: Struct that holds:
  - `index`: connection ID (index of the input/output)
  - `nonce`: nonce
  - `key` : symmetric key of the connection

- Connections: Map <index> -> <Connection>
  - for each input/output the Connection struct associated to it

## Runners

A runner file includes the logic of the `main()` function.

Two different runners are provided: `runner_native` and `runner_sgx`. Both of them implement a TCP server, listening to the SM port (which is the sum of EM port and Module ID).

The difference between the two runners is how the Module's Master Key is obtained:

- in `runner_native` the key is hardcoded by rust-sgx-gen.

- in `runner_sgx` the key is retrieved after performing Remote Attestation with the Deployer. The public key of `ra_sp` (the deployer's application that performs RA) needs to be hardcoded in the code.
