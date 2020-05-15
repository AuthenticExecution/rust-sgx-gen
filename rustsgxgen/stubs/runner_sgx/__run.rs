use std::net::{TcpListener, TcpStream};
use crate::__authentic_execution::authentic_execution::{EM_PORT, MODULE_ID, handle_entrypoint, debug};
extern crate base64;

use ra_enclave::EnclaveRaContext;

lazy_static! {
    pub static ref MODULE_KEY: String = remote_attestation().unwrap();
    pub static ref SP_VKEY_PEM: &'static str = "__SP_VKEY_PEM__";
}


fn handle_client(mut stream: TcpStream) {
    let payload = match reactive_net::read_message(&mut stream) {
        Ok(p) => p,
        Err(e) => {
            debug(&format!("{}", e));
            return;
        }
    };

    let resp = handle_entrypoint(&payload);

    if let Err(e) = reactive_net::write_result(&mut stream, &resp) {
        debug(&format!("{}", e));
    }
}


fn remote_attestation() -> std::io::Result<String> {
    let port = *EM_PORT + *MODULE_ID;
    let listener = TcpListener::bind(("0.0.0.0", port))?;

    let mut stream = listener.accept()?.0;

    debug("Connected to ra_client");
    let context = match EnclaveRaContext::init(*SP_VKEY_PEM) {
        Ok(c) => c,
        Err(e) => {
            debug(&format!("{:?}", e));
            panic!("{:?}", e);
        }
    };

    debug("Starting attestation process");
    let result = match context.do_attestation(&mut stream) {
        Ok(r) => r,
        Err(e) => {
            debug(&format!("{:?}", e));
            panic!("{:?}", e);
        }
    };

    debug("Remote attestation succeeded");

    Ok(base64::encode(&result.1))
}


pub fn run() -> std::io::Result<()> {
    let port = *EM_PORT + *MODULE_ID;

    debug("Waiting for attestation");

    // obtain the module's symmetric key
    let _ = *MODULE_KEY; //to trigger the remote attestation

    // authentic execution
    let host = format!("127.0.0.1:{}", port); // no one from outside can access SM

    debug(&format!("Listening on {}", host));
    let listener = TcpListener::bind(host)?;

    for stream in listener.incoming() {
        debug("Received connection");
        match stream {
            Ok(s) => handle_client(s),
            Err(_) => debug("ERROR unwrapping the stream")
        }
        debug("Connection ended\n");
    }
    Ok(())
}
