use std::net::{TcpListener, TcpStream};
use crate::{info, error};
use crate::__authentic_execution::authentic_execution::{MODULE_NAME, EM_PORT, MODULE_ID, NUM_THREADS, handle_entrypoint};
use threadpool::ThreadPool;

lazy_static! {
    pub static ref MODULE_KEY: String = String::from("___MODULE_KEY___");
}


fn handle_client(mut stream: TcpStream) {
    let payload = match reactive_net::read_message(&mut stream) {
        Ok(p) => p,
        Err(e) => {
            error!(&format!("{}", e));
            return;
        }
    };

    let resp = handle_entrypoint(&payload);

    if let Err(e) = reactive_net::write_result(&mut stream, &resp) {
        error!(&format!("{}", e));
    }
}


pub fn run() -> std::io::Result<()> {
    let port = *EM_PORT + *MODULE_ID;
    let pool = ThreadPool::new(*NUM_THREADS);

    let host = format!("127.0.0.1:{}", port); // no one from outside can access SM

    info!(&format!("Listening on {}", host));
    let listener = TcpListener::bind(host)?;

    for stream in listener.incoming() {
        //debug!("Received connection");
        match stream {
            Ok(s) => pool.execute(|| { handle_client(s) } ),
            Err(_) => error!("ERROR unwrapping the stream")
        }
        //debug!("Connection ended");
    }
    Ok(())
}
