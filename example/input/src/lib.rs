// Some imports / other stuff..

//@ sm_output(button_pressed)
//@ sm_output(output1)

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
