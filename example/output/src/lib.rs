#[macro_use] extern crate lazy_static;

extern crate network_lib;

mod __authentic_execution;
pub mod __run;

#[allow(unused_imports)] use __authentic_execution::authentic_execution;
#[allow(unused_imports)] use network_lib::{ResultCode, ResultMessage};

// Some imports / other stuff..

//@ sm_output(button_pressed)
pub fn button_pressed(data : &[u8]) {
    authentic_execution::debug("OUTPUT: button_pressed");
	let id : u16 = 0;

    authentic_execution::handle_output(id, data);
}

//@ sm_output(output1)
pub fn output1(data : &[u8]) {
    authentic_execution::debug("OUTPUT: output1");
	let id : u16 = 1;

    authentic_execution::handle_output(id, data);
}


//@ sm_entry
pub fn press_button(_data : &[u8]) -> ResultMessage {
    authentic_execution::debug("ENTRYPOINT: press_button");

    button_pressed(&[]);

    authentic_execution::success(None)
}

//@ sm_input
pub fn input1(data : &[u8]) {
    authentic_execution::debug("INPUT: input1");

    output1(data);
}

// Some user-defined functions..
