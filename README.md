# rust-sgx-gen

Automatic code generator for SGX/native modules of the [Authentic Execution framework](https://github.com/gianlu33/authentic-execution).

## Installation

```bash
# Install rust-sgx-gen - you must be on the root of this repository
pip install .
```

## Run

Generally, `rust-sgx-gen` is used within [`reactive-tools`](https://github.com/gianlu33/reactive-tools), so user intervention is not needed. To try it anyway:

```bash
# Check helper
rust-sgx-gen -h

# generate code and create output of a SGX module
### <input_fldr>: input folder of the Rust module
### <output_fldr>: output folder of the Rust module + the generated code
### <module_id>: ID of the module
### <reactive_port>: port used by the local Event Manager to listen for events
### <result_json>: a result JSON file containing the description of the module
### <runner>: either "sgx" or "native", depending on the nature of the module
### <ra_sp_pubkey>: path to ra_sp public key (for Remote Attestation - only SGX)
rust-sgx-gen -i <input_fldr> -o <output_fldr> -m <module_id> -e <reactive_port> -p <result_json> -r <runner> -s <ra_sp_pubkey>
```

## General rules

The input is a **Rust Cargo library**, created using the command `cargo new <name> --lib`

- A `main.rs` **should not** exist
- `[lib]` or `[[bin]]` sections in the `Cargo.toml` file **should not** exist

- The developer is free to implement his own code (files, functions, data structures, external dependencies), but:
  - They still have to respect the rules above
  - They must be aware of the limitations of a SGX enclave (e.g. some std functions are not supported). Check [here](https://edp.fortanix.com/docs/concepts/rust-std/)

## Define inputs, outputs, entry points, requests, handlers

[Tutorial](https://github.com/gianlu33/authentic-execution/blob/master/docs/tutorial-develop-apps.md#develop-an-sgx-or-native-module)

## Helper functions

Some helper functions are provided.

### Prints

Print macros are available: `debug!`, `info!`, `warning!` and `error!`. All of them accept a single parameter, which must implement the `Display` trait. Notice that multiple parameters can be printed together by using the `format!` macro.

```rust
// This instruction prints to stdout the following string: `[sm1] DEBUG: hello, world!`
debug!("hello, world!"); 

// This instruction prints to stdout the following string: `[sm1] INFO: hello, sm 1:22!`
info!(&format!("Hello, sm {}:{}!", 1, 22));
```



**Note**: `debug!` normally is disabled. Which means that the macro does not print anything to stdout. To enable debug prints, the module has to be compiled with the feature `debug_prints`.

### Return values of entry points

As described above, an entry point must return a `ResultMessage` element. A developer can either:

- create his own `ResultMessage` by calling `ResultMessage::new(code, payload)`
  
- See [here](https://github.com/gianlu33/rust-sgx-libs/blob/master/reactive_net/src/result_message.rs) for more details
  
- use the helper functions provided by the framework:

  ```rust
  success(data)
  failure(code, data)
  ```

  - `code` is a `ResultCode` (see link above)
    - The result code for `success` is always `ResultCode::Ok` (0)
  - `data` is an `Option<Vec<u8>>` which is an optional return value of the entry point.

 ## Call the entry point of a module

### Using reactive-tools

```bash
# Call the entry point of a module (the arg flag is optional)
### <config>: the output JSON file of a previous deploy command
### <module_name>: the name of the module
### <entry_name>: the name of the entry point
### <args_ex>: byte array as hexadecimal string, e.g., "deadbeef"
reactive-tools call --config <config> --module <module_name> --entry <entry_name> --arg <args_hex>
```

### Manual

To manually call the entry point of a module, we must know its id. All the identifiers are printed in the output JSON file (flag `-p` of `rust-sgx-gen`).

The general rule is that the entry points are enumerated in order of appearance in the `lib.rs` file, starting from 2.

The first two IDs correspond to entry points used for Authentic Execution:

- ID 0 is `set_key`
- ID 1 is `handle_input`
- ID 2 is `handle_handler`

**Calling the module directly**

The module must be loaded inside the same machine of the caller (because it listens for connections from the loopback interface).

To call an entry point, we must send the following payload:

`<payload_length><entrypoint_id><data>`

Where:

- `entrypoint_id` is 16 bits
- `data` can be omitted

One can use the [`reactive_net`](https://github.com/gianlu33/rust-sgx-libs/tree/master/reactive_net) utility functions to send more easily a message (using `write_message`)

**Calling the module indirectly**

We can call an entry point by sending the corresponding command to its Event Manager. We can connect to the EM from any machine connected to Internet.

The payload is the following:

`<command_id><payload_length><sm_id><entrypoint_id><data>`

Where:

- `command_id` is `CommandCode::CallEntrypoint` (16 bits)
- `payload_length` does not include `command_id`
- `sm_id` is the module id (provided as input to rust-sgx-gen, also present in the output JSON file)
- `entrypoint_id` and `data` are the same as before

We can use the helper function `write_command` of `reactive_net` to send this kind of message easily.
