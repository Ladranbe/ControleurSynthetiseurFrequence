/*******************************************************************************
Copyright 2016 Microchip Technology Inc. (www.microchip.com)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

To request to license the code under the MLA license (www.microchip.com/mla_license), 
please contact mla_licensing@microchip.com
*******************************************************************************/

#ifndef SYSTEM_H
#define SYSTEM_H

#include <xc.h>
#include <stdbool.h>

#include <stdint.h>

#include "buttons.h"
#include "leds.h"

#include "io_mapping.h"

#include "usb_config.h"
#include <stdint.h>

#define DRV_SPI_CONFIG_CHANNEL_1_ENABLE

#define REFERENCE_FREQUENCY ((uint32_t)100e6)

#define UV_RANGE_MAX_BOUNDARY ((uint32_t)2080e6)
#define UV_RANGE_MIN_BOUNDARY ((uint32_t)1040e6)
#define CHANNEL_SPACING ((int)40e3)


#define MAIN_RETURN void

/*** System States **************************************************/
typedef enum
{
    SYSTEM_STATE_USB_START,
    SYSTEM_STATE_USB_SUSPEND,
    SYSTEM_STATE_USB_RESUME
} SYSTEM_STATE;


//Function Latch type
typedef volatile union
{
    uint32_t fullLatch;                     //Indicates the total value of the register
    struct{                                 //Bitfields of the Function Latch
        uint8_t FUNCTION_LATCH_CTRL_BITS:2; //This value is 2 for the function latch
        uint8_t COUNTER_RESET:1;            //Counter Reset=0 => normal operation, 1 => R, A, B counters held in reset
        uint8_t POWER_DOWN_1:1;             //CE  PD2  PD1
                                            //0    x    x   Asynchronous Power Down
                                            //1    x    0   Normal Operation
                                            //1    0    1   Asynchronous Power Down
                                            //1    1    1   Synchronous Power Down
        
        uint8_t MUXOUT_CONTROL:3;           //M3  M2  M1
                                            //0   0   0     Three-state output
                                            //0   0   1     Digital Lock detect
                                            //0   1   0     N Divider output
                                            //0   1   1     DVDD
                                            //1   0   0     R Divider output
                                            //1   0   1     N-Channel open-drain Lock detect
                                            //1   1   0     Serial Data output
                                            //1   1   1     DGND
        
        uint8_t PD_POLARITY:1;              //Phase Detector Polarity (0->negative, 1->positive)
        uint8_t CP_THREE_STATE:1;           //Charge Pump output (0->normal, 1->three-state)
        uint8_t FAST_LOCK_ENABLE:1;         //Fastlock enable  Fastlock mode
                                            //      0                 x     Fastlock disabled
                                            //      1                 0     Fastlock mode 1
                                            //      1                 1     Fastlock mode 2
        
        uint8_t FAST_LOCK_MODE:1;           //See FAST_LOCK_ENABLE for indications
        uint8_t TIMER_COUNTER_CTRL:4;       //Timeout range 3 to 63 PFD cycles
        uint8_t CURRENT_SETTING_1:3;        //Sets the maximum value of the charge pump output current depending on the Rset value
        uint8_t CURRENT_SETTING_2:3;        //See CURRENT_SETTING_1 for indications
        uint8_t POWER_DOWN_2:1;             //See POWER_DOWN_1 for indications
        uint8_t PRESCALER_VALUE: 2;         //P2  P1
                                            //0   0     8/9
                                            //0   1     16/17
                                            //1   0     32/33
                                            //1   1     64/65
    }fLatchBitfields;
}F_LATCH;

//Reference Counter Latch type
typedef volatile union
{
    uint32_t fullLatch;                         //Indicates the total value of the register
    struct{                                     //Bitfields of the Reference Counter Latch
        uint8_t R_COUNTER_CONTROL_BITS:2;       //This value is 0 for the Reference Counter Latch
        uint8_t REFERENCE_COUNTER_VALUE_0:6;    //LSBs of the Reference Counter value
        uint8_t REFERENCE_COUNTER_VALUE_1:8;    //MSBs of the Reference Counter value
        uint8_t ANTI_BACKLASH_WIDTH:2;          //ABP1  ABP2  Anti-backlash pulse width
                                                // 0     0    2.9ns
                                                // 0     1    1.3ns TEST MODE ONLY. DO NOT USE
                                                // 1     0    6.0ns
                                                // 1     1    2.9ns
        uint8_t TEST_MODE_BITS:2;               //Must be set to 0 for normal operation
        uint8_t LOCK_DETECT_PRECISION:1;        //0->3 cycles of phase delay < 15ns needed before lock detect, 1->5 cycles
        uint8_t RESERVED:3;                     //Must be set to 0 for normal operation
    }rCounterLatchBitfields;
}R_COUNTER_LATCH;

//AB Counter Latch type
typedef volatile union
{
    uint32_t fullLatch;                         //Indicates the total value of the register
    struct{                                     //Bitfields of the AB Counter Latch
        uint8_t AB_COUNTER_CONTROL_BITS:2;      //This value is 1 for the AB Counter Latch
        uint8_t A_COUNTER_VALUE:6;              //A counter value
        uint8_t B_COUNTER_VALUE_0:8;            //LSBs of the B counter value
        uint8_t B_COUNTER_VALUE_1:5;            //MSBs of the B counter value
        uint8_t CP_GAIN:1;                      //Fastlock Enable  CP Gain
                                                //      0             0     Charge pump current setting 1 permanently used
                                                //      0             1     Charge pump current setting 2 permanently used
                                                //      1             0     Charge pump current setting 1 is used
                                                //      1             1     Charge pump current setting 2 is used during a period of time given by TIMER_COUNTER_CTRL before switching back to current setting 1
        
        uint8_t RESERVED:2;                     //Must be set to 0
    }abCounterLatchBitfields;
}AB_COUNTER_LATCH;

//Initialization Latch type
typedef volatile union
{
    uint32_t fullLatch;                     //Indicates the total value of the register
    struct{                                 //Bitfields of the initialization Latch
        uint8_t INITIALIZATION_LATCH_CTRL_BITS:2; //This value is 3 for the initialization latch
        uint8_t COUNTER_RESET:1;            //Counter Reset=0 => normal operation, 1 => R, A, B counters held in reset
        uint8_t POWER_DOWN_1:1;             //CE  PD2  PD1
                                            //0    x    x   Asynchronous Power Down
                                            //1    x    0   Normal Operation
                                            //1    0    1   Asynchronous Power Down
                                            //1    1    1   Synchronous Power Down
        
        uint8_t MUXOUT_CONTROL:3;           //M3  M2  M1
                                            //0   0   0     Three-state output
                                            //0   0   1     Digital Lock detect
                                            //0   1   0     N Divider output
                                            //0   1   1     DVDD
                                            //1   0   0     R Divider output
                                            //1   0   1     N-Channel open-drain Lock detect
                                            //1   1   0     Serial Data output
                                            //1   1   1     DGND
        
        uint8_t PD_POLARITY:1;              //Phase Detector Polarity (0->negative, 1->positive)
        uint8_t CP_THREE_STATE:1;           //Charge Pump output (0->normal, 1->three-state)
        uint8_t FAST_LOCK_ENABLE:1;         //Fastlock enable  Fastlock mode
                                            //      0                 x     Fastlock disabled
                                            //      1                 0     Fastlock mode 1
                                            //      1                 1     Fastlock mode 2
        
        uint8_t FAST_LOCK_MODE:1;           //See FAST_LOCK_ENABLE for indications
        uint8_t TIMER_COUNTER_CTRL:4;       //Timeout range 3 to 63 PFD cycles
        uint8_t CURRENT_SETTING_1:3;        //Sets the maximum value of the charge pump output current depending on the Rset value
        uint8_t CURRENT_SETTING_2:3;        //See CURRENT_SETTING_1 for indications
        uint8_t POWER_DOWN_2:1;             //See POWER_DOWN_1 for indications
        uint8_t PRESCALER_VALUE: 2;         //P2  P1
                                            //0   0     8/9
                                            //0   1     16/17
                                            //1   0     32/33
                                            //1   1     64/65
    }iLatchBitfields;
}I_LATCH;

    
/*********************************************************************
* Function: void SYSTEM_Initialize( SYSTEM_STATE state )
*
* Overview: Initializes the system.
*
* PreCondition: None
*
* Input:  SYSTEM_STATE - the state to initialize the system into
*
* Output: None
*
********************************************************************/
void SYSTEM_Initialize( SYSTEM_STATE state );

/*********************************************************************
* Function: void SYSTEM_Tasks(void)
*
* Overview: Runs system level tasks that keep the system running
*
* PreCondition: System has been initalized with SYSTEM_Initialize()
*
* Input: None
*
* Output: None
*
********************************************************************/
//void SYSTEM_Tasks(void);
#define SYSTEM_Tasks()

#endif //SYSTEM_H
