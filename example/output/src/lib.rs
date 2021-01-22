#[macro_use] extern crate lazy_static;

extern crate reactive_net;

mod __authentic_execution;
pub mod __run;

#[allow(unused_imports)] use __authentic_execution::authentic_execution;
#[allow(unused_imports)] use __authentic_execution::authentic_execution::{MODULE_NAME, success, failure, handle_output, handle_request, Error};
#[allow(unused_imports)] use reactive_net::{ResultCode, ResultMessage};

// Imports and other stuff

//@ sm_output(button_pressed)
pub fn button_pressed(data : &[u8]) {
    debug!("OUTPUT: button_pressed");
	let id : u16 = 16384;

    handle_output(id, data);
}

//@ sm_output(output1)
pub fn output1(data : &[u8]) {
    debug!("OUTPUT: output1");
	let id : u16 = 16385;

    handle_output(id, data);
}


//@ sm_request(get_value)
pub fn get_value(data : &[u8]) -> Result<Vec<u8>, Error> {
    debug!("REQUEST: get_value");
	let id : u16 = 32768;

    handle_request(id, data)
}


//@ sm_entry
pub fn press_button(_data : &[u8]) -> ResultMessage {
    debug!("ENTRYPOINT: press_button");

    button_pressed(&[]);

    success(None)
}

//@ sm_input
pub fn input1(data : &[u8]) {
    info!("INPUT: input1");

    output1(data);
}

//@ sm_handler
pub fn handler_value(_data : &[u8]) -> Vec<u8> {
    debug!("HANDLER: handler_value");

    vec!(1,2,3,4)
}

// User-defined functions and other stuff
