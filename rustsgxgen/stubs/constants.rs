    lazy_static! {{
        pub static ref MODULE_ID: u16 = {id};
        pub static ref MODULE_NAME: &'static str = "{name}";
        pub static ref EM_PORT: u16 = {em_port};
        pub static ref NUM_THREADS: usize = 1; //TODO assign custom value during code generation
        static ref INPUTS: std::collections::HashMap<u16, fn(&[u8])> = {{
            #[allow(unused_mut)]
            let mut m = std::collections::HashMap::new();
    {inputs}
            m
        }};
        static ref ENTRYPOINTS: std::collections::HashMap<u16, fn(&[u8]) -> ResultMessage> = {{
            let mut m = std::collections::HashMap::new();
            m.insert(0, set_key_wrapper as fn(&[u8]) -> ResultMessage);
            m.insert(1, attest_wrapper as fn(&[u8]) -> ResultMessage);
            m.insert(2, handle_input_wrapper as fn(&[u8]) -> ResultMessage);
            m.insert(3, handle_handler_wrapper as fn(&[u8]) -> ResultMessage);
    {entrypoints}
            m
        }};
        static ref HANDLERS: std::collections::HashMap<u16, fn(&[u8]) -> Vec<u8>> = {{
            #[allow(unused_mut)]
            let mut m = std::collections::HashMap::new();
    {handlers}
            m
        }};
    }}
