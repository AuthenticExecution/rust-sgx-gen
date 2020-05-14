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

### `runner_nosgx_simple`

Simple TCP server (no SGX) which listens for connections (serially) and calls its entrypoints
- The port is 4000 + MODULE_ID

### `runner_nosgx`

Runner for SM to perform Authentic Execution without using Intel SGX. It implements a TCP server

- EM port is passed as argument
  - SM port is: `EM port + SM ID`

- The TCP server waits for entrypoint calls (quite much the same as `runner_nosgx_simple`)
- The handling of outputs is performed by the `send_to_em` function, which spawns a thread that sends the data to the EM

### `runner_sgx_noattestation`

Runner for SM to perform AE with Intel SGX. The mechanism is basically the same as `runner_nosgx`

### `runner_sgx`

The ultimate runner. It expands `runner_sgx_noattestation` by performing Remote Attestation with the deployer, in order to retrieve the symmetric Module Key.
