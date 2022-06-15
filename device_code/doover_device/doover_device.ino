// EXAMPLE ONLY

// Put any code that will be deployed to end device in this directory.
// For example, if you are using an Arduino project, put it in here.


// Anywhere you need to declare keys and settings specific to the device, you can specify them as below




// *********** DEV_EUI ***********

uint8_t MsbNodeDeviceEUI[8] = { {{ dev_eui_msb_array }} };
// The result of this line after downloading from Doover will be;
// uint8_t nodeDeviceEUI[8] = { 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08 };

// You can also get an LSB array:
uint8_t LsbNodeDeviceEUI[8] = { {{ dev_eui_lsb_array }} };
// The result of this line after downloading from Doover will be;
// uint8_t nodeDeviceEUI[8] = { 0x08, 0x07, 0x06, 0x05, 0x04, 0x03, 0x02, 0x01 };



// *********** APP_EUI or JOIN_EUI ***********

uint8_t MsbNodeAppEUI[8] = { {{ join_eui_msb_array }} };
// The result of this line after downloading from Doover will be;
// uint8_t nodeAppEUI[8] = { 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08 };

uint8_t LsbNodeAppEUI[8] = { {{ join_eui_lsb_array }} };
// The result of this line after downloading from Doover will be;
// uint8_t nodeAppEUI[8] = { 0x08, 0x07, 0x06, 0x05, 0x04, 0x03, 0x02, 0x01 };



// *********** APP_KEY ***********

uint8_t MsbNodeAppKey[16] = { {{ app_key_msb_array }} };
// The result of this line after downloading from Doover will be;
// uint8_t nodeAppEUI[8] = { 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F };

uint8_t LsbNodeAppKey[16] = { {{ app_key_lsb_array }} };
// The result of this line after downloading from Doover will be;
// uint8_t nodeAppEUI[8] = { 0x0F, 0x0E, 0x0D, 0x0C, 0x0B, 0x0A, 0x09, 0x08, 0x07, 0x06, 0x05, 0x04, 0x03, 0x02, 0x01, 0x00 };

