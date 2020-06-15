// Imports and other stuff

//@ sm_output(button_pressed)
//@ sm_output(output1)

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

// User-defined functions and other stuff
