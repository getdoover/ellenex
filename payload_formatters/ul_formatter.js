// For more information visit the TTS Documentation
// https://www.thethingsindustries.com/docs/integrations/payload-formatters/javascript/uplink-decoder/

// This function takes the raw bytes from the device's uplink message
// And converts it to JSON

function decodeUplink(input) {

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