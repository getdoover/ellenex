// For more information visit the TTS Documentation
// https://www.thethingsindustries.com/docs/integrations/payload-formatters/javascript/downlink-encoder/

// This function takes a JSON message that is scheduled for downlink to the device,
// And converts it to bytes to send to the device over lora

function encodeDownlink(input) {
    return {
        bytes: [1, 2, 3],
        fPort: 1
    }
}




// For more information visit the TTS Documentation
// https://www.thethingsindustries.com/docs/integrations/payload-formatters/javascript/downlink-decoder/

// This function takes the raw bytes from a downlink message
// And converts it to JSON

function decodeDownlink(input) {

    // Input object has the following structure :
    // {
    //     "bytes": [1, 2, 3],
    //     "fPort": 1
    // }

    return {
        data: {
          bytes: input.bytes
        }
    };
}