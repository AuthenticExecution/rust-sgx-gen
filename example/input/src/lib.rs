// Imports and other stuff

//@ sm_output(button_pressed)
//@ sm_output(output1)

//@ sm_request(get_value)

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
