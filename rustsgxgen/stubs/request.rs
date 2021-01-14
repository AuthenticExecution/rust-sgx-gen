
pub fn {name}(data : &[u8]) -> Result<Vec<u8>, Error> {{
    debug!("REQUEST: {name}");
	let id : u16 = {id};

    handle_request(id, data)
}}
