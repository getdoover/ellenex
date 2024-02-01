// For more information visit the TTS Documentation
// https://www.thethingsindustries.com/docs/integrations/payload-formatters/javascript/uplink-decoder/

// This function takes the raw bytes from the device's uplink message
// And converts it to JSON

function decodeUplink(input) {
  switch (input.fPort) {
    case 15:
    case 1:
      // throw an error if length of Bytes is not 8
      if (input.bytes.length != 8) {
        return {
          errors: ['Invalid uplink payload: length is not 8 byte'],
        };
      }

      let sensorRange = 20; // 20 metres
      let liquidDensity = 1.0; // Water = 1.0, Diesel = 0.85, Petrol = 0.75

      let sensorReading = readHex2bytes(input.bytes[3], input.bytes[4]);
      let temperatureReading = readHex2bytes(input.bytes[5], input.bytes[6]);
      let batteryVoltage = input.bytes[7] * 0.1;
      batteryVoltage = batteryVoltage * 1.125 // compensate for apparent drop

      let level_mm = decodePLV3Sensor(sensorReading, temperatureReading, sensorRange, liquidDensity)
      // let level_cm = Number((level_mm / 10).toFixed(0))
      let level_cm = Number(level_mm.toFixed(0))

      var data = {
        level: level_cm,
        batteryVoltage: +batteryVoltage.toFixed(1),
      }

      data.doover_channels = {
        ui_state : {
            state : {
                children : {
                    details_submodule : {
                        children : {
                            rawlevel : {
                                currentValue : data.level
                            },
                            rawBattery : {
                                currentValue : data.batteryVoltage
                            }
                        }
                    },
                }
            }
        }
      }

      return {
        data: data
      };
      
      break;
    default:
      return {
        errors: ['Unknown FPort: please use fPort 1 or 15'],
      };
  }
}

/*
 * The readHex2bytes function is to decode a signed 16-bit integer
 * represented by 2 bytes.  
 */
function readHex2bytes(byte1, byte2) {
  let result = (byte1 << 8) | byte2;  // merge the two bytes
  // check whether input is signed as a negative number
  // by checking whether significant bit (leftmost) is 1
  let negative = byte1 & 0x80;
  // process negative value
  if (negative) {
    //result = ~(0xFFFF0000 | (result - 1)) * (-1);  // minus 1 and flip all bits
    result = result - 0x10000;
  }
  return result;
}


function decodePLV3Sensor(sensorReading, temperatureReading, sensorRange, liquidDensity) {

  const k = 0.01907
  const m = 0.007
  const b = -0.35

  let L1 = ((temperatureReading - 1638.3) * sensorRange) / 13106.4
  let L2 = (k * sensorReading * m) + b
  let level = (L1 - (L2*10)) / liquidDensity
  
  return level
}