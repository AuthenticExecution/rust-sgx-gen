# rust-sgx-gen

Automatic code generator for Rust libraries, to setup all the necessary for an Authentic Execution module.

## How to use it

Install the module by running `pip install <root_path>`

Run the generator through command line

- Run `rust-sgx-gen --help` for more information

## General rules

The input is a **Rust Cargo library**, created using the command `cargo new <name> --lib`

- A `main.rs` should not exist
- `[lib]` or `[[bin]]` sections in the `Cargo.toml` file should not exist

- The developer is free to implement his own code (files, functions, data structures, external dependencies), but:
  - He still has to respect the rules above
  - He must be aware of the limitations of a SGX enclave (e.g. some std functions are not supported). Check [here](https://edp.fortanix.com/docs/concepts/rust-std/)

## Define inputs, outputs, entrypoints

Inputs, outputs, entrypoints have to be defined in the `lib.rs` file (other files won't be checked for that). We use annotations (special comments) to define them.

**Outputs**

To define an output, it is sufficient to add the annotation somewhere in the file. The code is automatically generated.

Example:

```rust
//@ sm_output(button_pressed)
```

Here, we define an output called `button_pressed`

The signature of the output is:

```rust
pub fn <name>(data : &[u8]);
```

**Inputs**

For inputs, we have to provide an implementation. The signature is the same as for outputs.

Example:

```rust
//@ sm_input
pub fn input1(data : &[u8]) {
    button_pressed(data);
}
```

**Entrypoints**

Entrypoints emulate the `ECALLS` in `SGX SDK`. Can be called by an external entity.

Example:

```rust
//@ sm_entry
pub fn press_button(data : &[u8]) -> ResultMessage {
    button_pressed(data);

    authentic_execution::success(None)
}
```

As you can see here, we must provide a return value, of type `ResultMessage` (see below).

## Helper functions

Some helper functions are provided.

### Debug prints

```rust
authentic_execution::debug("hello, world!");
```

This function will print to stdout the message (which is a `&str`), as well as the module name: `[sm1]  hello, world!`

### Return values of entrypoints

As described above, an entrypoint must return a `ResultMessage` element. A developer can either:

- create his own `ResultMessage` by calling `ResultMessage::new(code, payload)`
  - See [here](https://github.com/gianlu33/rust-sgx-libs/blob/master/network_lib/src/result_message.rs) for more details

- use the helper functions provided by the framework:

  ```rust
  authentic_execution::success(data)
  authentic_execution::failure(code, data)
  ```

  - `code` is a `ResultCode` (see link above)
  - `data` is an `Option<Vec<u8>>` which is an optional return value of the entrypoint.

 ## Call an entrypoint of a module

To call an entrypoint of a module, we must know its id. All the identifiers are printed in the output JSON file (flag `-p` of `rust-sgx-gen`).

The general rule is that the entrypoints are enumerated in order of appearance in the `lib.rs` file, starting from 2.

The first two IDs correspond to entrypoints used for Authentic Execution:

- ID 0 is `set_key` entrypoint
- ID 1 is `handle_input` entrypoint

### Call the module directly

The module must be loaded inside the same machine of the caller (because it listens for connections from the loopback interface).

To call an entrypoint, we must send the following payload:

`<payload_length><entrypoint_id><data>`

Where:

- `entrypoint_id` is 16 bits
- `data` can be omitted

One can use the [`network_lib`](https://github.com/gianlu33/rust-sgx-libs/tree/master/network_lib) utility functions to send more easily a message (using `write_message`)

### Call the module indirectly

We can call an entrypoint by sending the corresponding command to its Event Manager. We can connect to the EM from any machine connected to Internet.

The payload is the following:

`<command_id><payload_length><sm_id><entrypoint_id><data>`

Where:

- `command_id` is `CommandCode::CallEntrypoint` (16 bits)
- `payload_length` does not include `command_id`
- `sm_id` is the module id (provided as input to rust-sgx-gen, also present in the output JSON file)
- `entrypoint_id` and `data` are the same as before

We can use the helper function `write_command` of `network_lib` to send this kind of message easily.
