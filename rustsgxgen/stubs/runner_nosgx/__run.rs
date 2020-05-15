use std::net::{TcpListener, TcpStream};
use crate::__authentic_execution::authentic_execution::{EM_PORT, MODULE_ID, handle_entrypoint, debug};

lazy_static! {
    pub static ref MODULE_KEY: String = String::from("___MODULE_KEY___");
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


pub fn run() -> std::io::Result<()> {
    let port = *EM_PORT + *MODULE_ID;
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
