pub mod authentic_execution {
    extern crate base64;
    extern crate reactive_crypto;
    extern crate reactive_net;

    use std::collections::HashMap;
    use std::sync::Mutex;
    use std::thread;
    use std::net::TcpStream;

    use reactive_net::{ResultCode, CommandCode, ResultMessage, CommandMessage};
    use reactive_crypto::Encryption;
    use crate::__run::MODULE_KEY;

    #[derive(Debug)]
    pub enum Error {
        NoConnectionForRequest,
        NoConnectionForOutput,
        InternalError,
        CryptoError,
        NetworkError,
        PayloadTooLarge,
        BadResponse
    }

    impl std::fmt::Display for Error {
        fn fmt(&self, f: &mut std::fmt::Formatter<'_>)
            -> Result<(), std::fmt::Error> {
                write!(f, "{:?}", self)
            }
    }

    enum IndexType {
        Input,
        Output,
        Request,
        Handler
    }

    impl IndexType {
        pub fn from_u16(value : u16) -> IndexType {
            match value {
                v if v < 16384  => IndexType::Input,
                v if v < 32768  => IndexType::Output,
                v if v < 49152  => IndexType::Request,
                _               => IndexType::Handler
            }
        }
    }

    mod connection {
        use reactive_crypto::Encryption;

        pub struct Connection {
            index : u16,
            nonce : u16,
            key : Vec<u8>,
            encryption : Encryption
        }

        impl Connection {
            pub fn new(index : u16, nonce : u16, key : Vec<u8>, encryption : Encryption) -> Connection {
                Connection {
                    index,
                    nonce,
                    key,
                    encryption
                }
            }

            pub fn get_index(&self) -> u16 {
                self.index
            }

            pub fn get_nonce(&self) -> u16 {
                self.nonce
            }

            pub fn increment_nonce(&mut self) {
                self.nonce += 1;
            }

            pub fn get_key(&self) -> &Vec<u8> {
                &self.key
            }

            pub fn get_encryption(&self) -> &Encryption {
                &self.encryption
            }
        }
    }

    #[allow(dead_code)]
    pub fn data_to_u16(data : &[u8]) -> u16 {
        u16::from_be_bytes([data[0], data[1]])
    }

    #[allow(dead_code)]
    pub fn data_to_u32(data : &[u8]) -> u32 {
        u32::from_be_bytes([data[0], data[1], data[2], data[3]])
    }

    #[allow(dead_code)]
    pub fn u16_to_data(val : u16) -> [u8; 2] {
        val.to_be_bytes()
    }

    pub fn success(data : Option<Vec<u8>>) -> ResultMessage {
        ResultMessage::new(ResultCode::Ok, data)
    }

    pub fn failure(code : ResultCode, data : Option<Vec<u8>>) -> ResultMessage {
        ResultMessage::new(code, data)
    }

    #[cfg(feature = "debug_prints")]
    #[macro_export]
    macro_rules! debug {
        ($msg:expr) => {{
                println!("[{}] DEBUG: {}", &*MODULE_NAME, $msg);
        }};
    }
    #[cfg(not(feature = "debug_prints"))]
    #[macro_export]
    macro_rules! debug {
        ($( $args:expr ),*) => {{}};
    }
    #[macro_export]
    macro_rules! info {
        ($msg:expr) => {{
                println!("[{}] INFO: {}", &*MODULE_NAME, $msg);
        }};
    }
    #[macro_export]
    macro_rules! error {
        ($msg:expr) => {{
                eprintln!("[{}] ERROR: {}", &*MODULE_NAME, $msg);
        }};
    }
    #[macro_export]
    macro_rules! warning {
        ($msg:expr) => {{
                eprintln!("[{}] WARNING: {}", &*MODULE_NAME, $msg);
        }};
    }

    /// This is the only interface to the software module from outside
    /// Each request has to be sent to this function
    #[allow(dead_code)]
    pub fn handle_entrypoint(data : &[u8]) -> ResultMessage {
        // The payload is: [entry_id - data]

        if data.len() < 2 {
            return failure(ResultCode::IllegalPayload, None)
        }

        let id = data_to_u16(data);

        let entry = match ENTRYPOINTS.get(&id) {
            Some(e) => e,
            None => return failure(ResultCode::BadRequest, None)
        };

        entry(&data[2..])
    }

    pub fn set_key_wrapper(data : &[u8]) -> ResultMessage  {
        // The payload is: [encryption_type - index - nonce - cipher]
        debug!("ENTRYPOINT: set_key");

        if data.len() < 7 {
            return failure(ResultCode::IllegalPayload, None)
        }

        set_key(data[0], &data[1..3], &data[3..5], &data[5..7], &data[7..])
    }

    fn set_key(enc : u8, conn_id : &[u8], index : &[u8], nonce : &[u8], cipher : &[u8]) -> ResultMessage {
        // The tag is included in the cipher

        let mut ad = vec!(enc);
        ad.extend_from_slice(conn_id);
        ad.extend_from_slice(index);
        ad.extend_from_slice(nonce);

        let decoded_key = match base64::decode(&*MODULE_KEY) {
            Ok(k)   => k,
            Err(_)  => return failure(ResultCode::InternalError, None)
        };

        let key = match reactive_crypto::decrypt(cipher, &decoded_key, &ad, &Encryption::Aes) {
           Ok(k)    => k,
           Err(_)   => return failure(ResultCode::CryptoError, None)
        };

        let enc_type = match Encryption::from_u8(enc) {
            Some(e) => e,
            None    => return failure(ResultCode::CryptoError, None)
        };

        let index_u16 = data_to_u16(index);
        let conn_id_u16 = data_to_u16(conn_id);
        let conn = connection::Connection::new(index_u16, 0, key, enc_type);
        add_connection(conn_id_u16, conn);

        // if index is an output, add to "outputs"
        // if index is request, add to "requests"
        match IndexType::from_u16(index_u16) {
            IndexType::Output   => {
                add_output(index_u16, conn_id_u16);
            },
            IndexType::Request  => {
                add_request(index_u16, conn_id_u16);
            },
            _                   => {}
        }

        success(None)
    }

    pub fn handle_input_wrapper(data : &[u8]) -> ResultMessage  {
        // The payload is: [index - payload]
        debug!("ENTRYPOINT: handle_input");

        if data.len() < 2 {
            return failure(ResultCode::IllegalPayload, None)
        }

        handle_input(data_to_u16(data), &data[2..])
    }

    fn handle_input(conn_id : u16, payload : &[u8]) -> ResultMessage {
        // the index is not associated data because it is not sent by the `from` module, but by the event manager

        let mut map = CONNECTIONS.lock().unwrap();
        let conn = match map.get_mut(&conn_id) {
            Some(v) => v,
            None => return failure(ResultCode::BadRequest, None)
        };

        let nonce = conn.get_nonce();
        let data = match reactive_crypto::decrypt(payload, conn.get_key(), &u16_to_data(nonce), conn.get_encryption()) {
           Ok(d) => d,
           Err(_) => return failure(ResultCode::CryptoError, None)
        };

        conn.increment_nonce();
        let index = &conn.get_index();
        drop(map); // fix: if the input calls an output, the CONNECTIONS map has to be free

        let handler = match INPUTS.get(index) {
            Some(h) => h,
            None => return failure(ResultCode::BadRequest, None)
        };

        handler(&data);

        success(None)
    }

    pub fn handle_handler_wrapper(data : &[u8]) -> ResultMessage  {
        // The payload is: [index - payload]
        debug!("ENTRYPOINT: handle_request");

        if data.len() < 2 {
            return failure(ResultCode::IllegalPayload, None)
        }

        handle_handler(data_to_u16(data), &data[2..])
    }

    fn handle_handler(conn_id : u16, payload : &[u8]) -> ResultMessage {
        // the index is not associated data because it is not sent by the `from` module, but by the event manager

        // get connection from map
        let mut map = CONNECTIONS.lock().unwrap();
        let conn = match map.get_mut(&conn_id) {
            Some(v) => v,
            None => return failure(ResultCode::BadRequest, None)
        };

        let nonce = conn.get_nonce();
        let key = conn.get_key();
        let encryption = conn.get_encryption();
        let index = conn.get_index();

        // decrypt payload
        let data = match reactive_crypto::decrypt(payload, key, &u16_to_data(nonce), encryption) {
           Ok(d) => d,
           Err(_) => return failure(ResultCode::CryptoError, None)
        };

        // execute handler
        let handler = match HANDLERS.get(&index) {
            Some(h) => h,
            None => return failure(ResultCode::BadRequest, None)
        };

        let result = handler(&data);

        // encrypt response
        let response = match reactive_crypto::encrypt(&result, key,
                                        &u16_to_data(nonce+1), encryption) {
           Ok(p)    => p,
           Err(_)   => return failure(ResultCode::CryptoError, None)
        };

        // increment nonce two times (two crypto operations)
        // TODO what if something is wrong in the middle
        conn.increment_nonce();
        conn.increment_nonce();

        success(Some(response))
    }

    #[allow(dead_code)] // this is needed if we have no outputs to avoid warnings
    pub fn handle_output(index : u16, data : &[u8]) {
        let connections = match get_connections_from_output(index) {
            Some(vec)       => vec,
            None            => return // no connections associated to the output
        };

        let mut map = CONNECTIONS.lock().unwrap();

        for conn_id in connections {
            let conn = match map.get_mut(&conn_id) {
                Some(c)     => c,
                None        => {
                    error!(&format!("{}", Error::NoConnectionForOutput));
                    continue; // or break? Btw this SHOULD NEVER happen
                }
            };

            let nonce = conn.get_nonce();
            let payload = match reactive_crypto::encrypt(data, conn.get_key(),
                                            &u16_to_data(nonce), conn.get_encryption()) {
               Ok(p) => p,
               Err(e) => {
                   error!(&format!("{}", e));
                   return; //encryption failed (there's nothing we can do in this case)
               }
            };

            conn.increment_nonce();
            send_to_em(conn_id, payload);
        }
    }

    #[allow(dead_code)] // this is needed if we have no outputs to avoid warnings
    pub fn handle_request(index : u16, data : &[u8]) -> Result<Vec<u8>, Error> {
        // find connection associated to the request
        let conn_id = match get_connection_from_request(index) {
            Some(c)     => c,
            None        => return Err(Error::NoConnectionForRequest)
        };

        // find all connections associated to the output
        let mut map = CONNECTIONS.lock().unwrap();
        let conn = match map.get_mut(&conn_id) {
            Some(v)     => v,
            None        => return Err(Error::InternalError) // it shouldn't happen
        };

        // encrypt payload
        let nonce = conn.get_nonce();
        let key = conn.get_key();
        let encryption = conn.get_encryption();

        let payload = match reactive_crypto::encrypt(data, key,
                                        &u16_to_data(nonce), encryption) {
           Ok(p)    => p,
           Err(_)   => return Err(Error::CryptoError)
        };

        // send payload
        let response = send_to_em_blocking(conn_id, payload)?;

        // Check fesponse
        let resp_body = match response.get_code() {
            ResultCode::Ok      => response.get_payload(),
            _                   => return Err(Error::BadResponse)
        };

        let resp_body = match resp_body {
            Some(p)     => p,
            None        => return Err(Error::BadResponse)
        };

        // decrypt response
        let data = match reactive_crypto::decrypt(resp_body, key,
                                        &u16_to_data(nonce+1), encryption) {
           Ok(d)    => d,
           Err(_)   => return Err(Error::CryptoError)
        };

        // increment nonce two times (two crypto operations)
        //TODO: what happens in case of failure in the middle?
        conn.increment_nonce();
        conn.increment_nonce();

        Ok(data)
    }

    /// Send the output payload to the event manager, which will forward it to the input connected to the `index` output
    fn send_to_em(conn_id : u16, mut data : Vec<u8>) {
        thread::spawn(move || {
            let addr = format!("127.0.0.1:{}", *EM_PORT);

            debug!(&format!("Sending output with conn ID {} to EM", conn_id));

            let data_len = data.len();
            if data_len > 65531 {
                    error!("Data is too big. Aborting");
                    return;
            }

            let mut payload = Vec::with_capacity(data_len + 2);
            payload.extend_from_slice(&conn_id.to_be_bytes());
            payload.append(&mut data);

            let mut stream = match TcpStream::connect(addr) {
                Ok(s) => s,
                Err(_) => {
                    error!("Cannot connect to EM");
                    return;
                }
            };
            debug!("Connected to EM");

            let cmd = CommandMessage::new(CommandCode::ModuleOutput, Some(payload));

            if let Err(e) = reactive_net::write_command(&mut stream, &cmd) {
                error!(&format!("{}", e));
            }
        });
    }

    /// Send the output payload to the event manager, which will forward it to the handler connected to the `index` id
    /// Blocking: we will wait for a response
    fn send_to_em_blocking(conn_id : u16, mut data : Vec<u8>) -> Result<ResultMessage, Error> {
        let addr = format!("127.0.0.1:{}", *EM_PORT);

        debug!(&format!("Sending request with conn ID {} to EM", conn_id));

        // Create payload
        let data_len = data.len();
        if data_len > 65531 {
                return Err(Error::PayloadTooLarge);
        }

        let mut payload = Vec::with_capacity(data_len + 2);
        payload.extend_from_slice(&conn_id.to_be_bytes());
        payload.append(&mut data);

        // Connect to the EM
        let mut stream = match TcpStream::connect(addr) {
            Ok(s)   => s,
            Err(_)  => return Err(Error::NetworkError)
        };

        // Send command
        let cmd = CommandMessage::new(CommandCode::ModuleRequest, Some(payload));

        if let Err(_) = reactive_net::write_command(&mut stream, &cmd) {
            return Err(Error::NetworkError)
        }

        // Wait for response
        match reactive_net::read_result(&mut stream) {
            Ok(r)   => Ok(r),
            Err(_)  => Err(Error::NetworkError)
        }
    }

    // Variables: connections. Contains, for each connection, key, nonce, and handler index
    lazy_static! {
        static ref CONNECTIONS: Mutex<HashMap<u16, connection::Connection>> = {
            Mutex::new(HashMap::new())
        };
        static ref OUTPUTS: Mutex<HashMap<u16, Vec<u16>>> = {
            Mutex::new(HashMap::new())
        };
        static ref REQUESTS: Mutex<HashMap<u16, u16>> = {
            Mutex::new(HashMap::new())
        };
    }

    // Constants: Module's key, ID, Inputs, Outputs
{CONSTANTS}

    fn add_connection(conn_id : u16, conn : connection::Connection) {
        CONNECTIONS.lock().unwrap().insert(conn_id, conn);
    }

    fn add_output(out_id : u16, conn_id : u16) {
        //TODO if entry not in map, add entry with Vec containing only conn_id
        //TODO if entry in map, add conn_id to entry
        let mut map = OUTPUTS.lock().unwrap();

        match map.get_mut(&out_id) {
            Some(vec)   => {
                vec.push(conn_id);
            },
            None        => {
                map.insert(out_id, vec!(conn_id));
            }
        }
    }

    fn get_connections_from_output(out_id : u16) -> Option<Vec<u16>> {
        match OUTPUTS.lock().unwrap().get(&out_id) {
            Some(val)   => Some(val.to_vec()),
            None        => None
        }
    }

    fn add_request(req_id : u16, conn_id : u16) {
        REQUESTS.lock().unwrap().insert(req_id, conn_id);
    }

    fn get_connection_from_request(req_id : u16) -> Option<u16> {
        match REQUESTS.lock().unwrap().get(&req_id) {
            Some(val)   => Some(*val),
            None        => None
        }
    }
}
