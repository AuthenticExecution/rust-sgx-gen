use std::net::{TcpListener, TcpStream};
use crate::{debug, info, error};
use crate::__authentic_execution::authentic_execution::{MODULE_NAME, EM_PORT, MODULE_ID, NUM_THREADS, handle_entrypoint};
extern crate base64;
use threadpool::ThreadPool;

lazy_static! {
    pub static ref MODULE_KEY: String = remote_attestation().unwrap();
    pub static ref SP_VKEY_PEM: &'static str = "__SP_VKEY_PEM__";
}


fn handle_client(mut stream: TcpStream) {
    let payload = match reactive_net::read_message(&mut stream) {
        Ok(p) => p,
        Err(e) => {
            error!("{}", e);
            return;
        }
    };

    let resp = handle_entrypoint(&payload);

    if let Err(e) = reactive_net::write_result(&mut stream, &resp) {
        error!("{}", e);
    }
}


fn remote_attestation() -> std::io::Result<String> {
    info!("Waiting for attestation");
    let port = *EM_PORT + *MODULE_ID;

    let result = match sgx_attestation::do_attestation(port, *SP_VKEY_PEM) {
        Ok(r) => r,
        Err(e) => {
            error!("{:?}", e);
            panic!("{:?}", e);
        }
    };

    info!("Remote attestation succeeded");

    Ok(base64::encode(&result))
}

fn run_single_thread(listener : TcpListener) {
    for stream in listener.incoming() {
        //debug!("Received connection");
        match stream {
            Ok(s)   => handle_client(s),
            Err(_)  => error!("ERROR unwrapping the stream")
        }
        //debug!("Connection ended");
    }
}

fn run_multithread(listener : TcpListener) {
    let pool = ThreadPool::new(*NUM_THREADS - 1);

    for stream in listener.incoming() {
        //debug!("Received connection");
        match stream {
            Ok(s)   => pool.execute(|| { handle_client(s) } ),
            Err(_)  => error!("ERROR unwrapping the stream")
        }
        //debug!("Connection ended");
    }
}

pub fn run() -> std::io::Result<()> {
    let port = *EM_PORT + *MODULE_ID;

    debug!("Waiting for attestation");
    let _ = *MODULE_KEY; // trigger the remote attestation

    // authentic execution
    let host = format!("127.0.0.1:{}", port); // no one from outside can access SM

    info!("Listening on {}", host);
    let listener = TcpListener::bind(host)?;

    match *NUM_THREADS {
        0   => panic!("NUM_THREADS is zero"),
        1   => run_single_thread(listener),
        _   => run_multithread(listener)
    }

    Ok(())
}
