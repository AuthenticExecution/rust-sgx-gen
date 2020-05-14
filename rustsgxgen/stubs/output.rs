
pub fn {name}(data : &[u8]) {{
    authentic_execution::debug("OUTPUT: {name}");
	let id : u16 = {id};

    authentic_execution::handle_output(id, data);
}}
