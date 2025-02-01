##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2015 Bart de Waal <bart@waalamo.com>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <http://www.gnu.org/licenses/>.
##

import sigrokdecode as srd
from math import ceil

RX = 0
TX = 1
rxtx_channels = ('RX', 'TX')

class No_more_data(Exception):
    '''This exception is a signal that we should stop parsing an ADU as there
    is no more data to parse.'''
    pass

class Data:
    '''The Data class is used to hold the bytes from the serial decode.'''
    def __init__(self, start, end, data):
        self.start = start
        self.end = end
        self.data = data

class Modbus_ADU:
    '''An Application Data Unit is what Modbus calls one message.
    Protocol decoders are supposed to keep track of state and then provide
    decoded data to the backend as it reads it. In Modbus' case, the state is
    the ADU up to that point. This class represents the state and writes the
    messages to the backend.
    This class is for the common infrastructure between CS and SC. It should
    not be used directly, only inhereted from.'''

    def __init__(self, parent, start, write_channel, annotation_prefix):
        self.data = [] # List of all the data received up to now
        self.parent = parent # Reference to the decoder object
        self.start = start
        self.last_read = start # The last moment parsed by this ADU object
        self.write_channel = write_channel
        self.last_byte_put = -1
        self.annotation_prefix = annotation_prefix
        # Any Modbus message needs to be at least 4 bytes long. The Modbus
        # function may make this longer.
        self.minimum_length = 4

        # This variable is used by an external function to determine when the
        # next frame should be started.
        self.startNewFrame = False

        # If there is an error in a frame, we'd like to highlight it. Keep
        # track of errors.
        self.hasError = False

    def add_data(self, start, end, data):
        '''Let the frame handle another piece of data.
        start: start of this data
        end: end of this data
        data: data as received from the UART decoder'''
        ptype, rxtx, pdata = data
        self.last_read = end
        if ptype == 'DATA':
            self.data.append(Data(start, end, pdata[0]))
            self.parse() # parse() is defined in the specific type of ADU.

    def puti(self, byte_to_put, annotation, message):
        '''This class keeps track of how much of the data has already been
        annotated. This function tells the parent class to write message, but
        only if it hasn't written about this bit before.
        byte_to_put: Only write if it hasn't yet written byte_to_put. It will
                     write from the start of self.last_byte_put+1 to the end
                     of byte_to_put.
        annotation: Annotation to write to, without annotation_prefix.
        message: Message to write.'''
        if byte_to_put > len(self.data) - 1:
            # If the byte_to_put hasn't been read yet.
            raise No_more_data

        if annotation == 'error':
            self.hasError = True

        if byte_to_put > self.last_byte_put:
            self.parent.puta(
                self.data[self.last_byte_put + 1].start,
                self.data[byte_to_put].end,
                self.annotation_prefix + annotation,
                message)
            self.last_byte_put = byte_to_put
            raise No_more_data

    def putl(self, annotation, message, maximum=None):
        '''Puts the last byte on the stack with message. The contents of the
        last byte will be applied to message using format.'''
        last_byte_address = len(self.data) - 1
        if maximum is not None and last_byte_address > maximum:
            return
        self.puti(last_byte_address, annotation,
                  message.format(self.data[-1].data))

    def close(self, message_overflow):
        '''Function to be called when next message is started. As there is
        always space between one message and the next, we can use that space
        for errors at the end.'''
        # TODO: Figure out how to make this happen for last message.
        data = self.data
        if len(data) < self.minimum_length:
            if len(data) == 0:
                # Sometimes happens with noise, safe to ignore.
                return
            self.parent.puta(
                data[self.last_byte_put].end, message_overflow,
                self.annotation_prefix + 'error',
                'Message too short or not finished')
            self.hasError = True
        if self.hasError and self.parent.options['scchannel'] != self.parent.options['cschannel']:
            # If we are decoding different channels (so client->server and
            # server->client messages can be separated) we like to mark blocks
            # containing errors. We don't do this when decoding the same
            # channel as both a client->server and server->client frame, and
            # one of those is bound to contain an error, making highlighting
            # frames useless.
            self.parent.puta(data[0].start, data[-1].end,
                             'error-indication', 'Frame contains error')
        if len(data) > 256:
            try:
                self.puti(len(data) - 1, 'error',
                    'Modbus data frames are limited to 256 bytes')
            except No_more_data:
                pass

    def check_crc(self, byte_to_put):
        '''Check the CRC code, data[byte_to_put] is the 2nd byte of the CRC.'''
        crc_byte1, crc_byte2 = self.calc_crc(byte_to_put)
        data = self.data
        if data[-2].data == crc_byte1 and data[-1].data == crc_byte2:
            self.puti(byte_to_put, 'crc', 'CRC correct')
        else:
            self.puti(byte_to_put, 'error',
                'CRC should be {} {}'.format(crc_byte1, crc_byte2))

    def half_word(self, start):
        '''Return the half word (16 bit) value starting at start bytes in. If
        it goes out of range it raises the usual errors.'''
        if (start + 1) > (len(self.data) - 1):
            # If there isn't enough length to access data[start + 1].
            raise No_more_data
        return self.data[start].data * 0x100 + self.data[start + 1].data

    def calc_crc(self, last_byte):
        '''Calculate the CRC, as described in the spec.
        The last byte of the CRC should be data[last_byte].'''
        if last_byte < 3:
            # Every Modbus ADU should be as least 4 long, so we should never
            # have to calculate a CRC on something shorter.
            raise Exception('Could not calculate CRC: message too short')

        result = 0xFFFF
        magic_number = 0xA001 # As defined in the modbus specification.
        for byte in self.data[:last_byte - 1]:
            result = result ^ byte.data
            for i in range(8):
                LSB = result & 1
                result = result >> 1
                if (LSB): # If the LSB is true.
                    result = result ^ magic_number
        byte1 = result & 0xFF
        byte2 = (result & 0xFF00) >> 8
        return (byte1, byte2)

    def parse_write_single_coil(self):
        '''Parse function 5, write single coil.'''
        self.minimum_length = 8

        self.puti(1, 'function', 'Function 5: Write Single Coil')

        address = self.half_word(2)
        self.puti(3, 'address',
            'Address 0x{:X} / {:d}'.format(address, address + 10000))

        raw_value = self.half_word(4)
        value = 'Invalid Coil Value'
        if raw_value == 0x0000:
            value = 'Coil Value OFF'
        elif raw_value == 0xFF00:
            value = 'Coil Value ON'
        self.puti(5, 'data', value)

        self.check_crc(7)

    def parse_write_single_register(self):
        '''Parse function 6, write single register.'''
        self.minimum_length = 8

        self.puti(1, 'function', 'Function 6: Write Single Register')

        address = self.half_word(2)
        self.puti(3, 'address',
            'Address 0x{:X} / {:d}'.format(address, address + 30000))

        value = self.half_word(4)
        value_formatted = 'Register Value 0x{0:X} / {0:d}'.format(value)
        self.puti(5, 'data', value_formatted)

        self.check_crc(7)

    def parse_diagnostics(self):
        '''Parse function 8, diagnostics. This function has many subfunctions,
        but they are all more or less the same.'''
        self.minimum_length = 8

        self.puti(1, 'function', 'Function 8: Diagnostics')

        diag_subfunction = {
            0: 'Return Query data',
            1: 'Restart Communications Option',
            2: 'Return Diagnostics Register',
            3: 'Change ASCII Input Delimiter',
            4: 'Force Listen Only Mode',
            10: 'Clear Counters and Diagnostic Register',
            11: 'Return Bus Message Count',
            12: 'Return Bus Communication Error Count',
            13: 'Return Bus Exception Error Count',
            14: 'Return Slave Message Count',
            15: 'Return Slave No Response Count',
            16: 'Return Slave NAK Count',
            17: 'Return Slave Busy Count',
            18: 'Return Bus Character Overrun Count',
            20: 'Return Overrun Counter and Flag',
        }
        subfunction = self.half_word(2)
        subfunction_name = diag_subfunction.get(subfunction,
                                                'Reserved subfunction')
        self.puti(3, 'data',
            'Subfunction {}: {}'.format(subfunction, subfunction_name))

        diagnostic_data = self.half_word(4)
        self.puti(5, 'data',
            'Data Field: {0} / 0x{0:04X}'.format(diagnostic_data))

        self.check_crc(7)

    def parse_mask_write_register(self):
        '''Parse function 22, Mask Write Register.'''
        self.minimum_length = 10
        data = self.data

        self.puti(1, 'function', 'Function 22: Mask Write Register')

        address = self.half_word(2)
        self.puti(3, 'address',
            'Address 0x{:X} / {:d}'.format(address, address + 30001))

        self.half_word(4) # To make sure we don't oveflow data.
        and_mask_1 = data[4].data
        and_mask_2 = data[5].data
        self.puti(5, 'data',
            'AND mask: {:08b} {:08b}'.format(and_mask_1, and_mask_2))

        self.half_word(6) # To make sure we don't oveflow data.
        or_mask_1 = data[6].data
        or_mask_2 = data[7].data
        self.puti(7, 'data',
            'OR mask: {:08b} {:08b}'.format(or_mask_1, or_mask_2))

        self.check_crc(9)

    def parse_not_implemented(self):
        '''Explicitly mark certain functions as legal functions, but not
        implemented in this parser. This is due to the author not being able to
        find anything (hardware or software) that supports these functions.'''
        # TODO: Implement these functions.

        # Mentioning what function it is is no problem.
        function = self.data[1].data
        functionname = {
            20: 'Read File Record',
            21: 'Write File Record',
            24: 'Read FIFO Queue',
            43: 'Read Device Identification/Encapsulated Interface Transport',
        }[function]
        self.puti(1, 'function',
            'Function {}: {} (not supported)'.format(function, functionname))

        # From there on out we can keep marking it unsupported.
        self.putl('data', 'This function is not currently supported')

class Modbus_ADU_SC(Modbus_ADU):
    '''SC stands for Server -> Client.'''
    def parse(self):
        '''Select which specific Modbus function we should parse.'''
        data = self.data

        # This try-catch is being used as flow control.
        try:
            server_id = data[0].data
            if 1 <= server_id <= 247:
                message = 'Slave ID: {}'.format(server_id)
            else:
                message = 'Slave ID {} is invalid'
            self.puti(0, 'server-id', message)

            function = data[1].data
            if function == 1 or function == 2:
                self.parse_read_bits()
            elif function == 3 or function == 4 or function == 23:
                self.parse_read_registers()
            elif function == 5:
                self.parse_write_single_coil()
            elif function == 6:
                self.parse_write_single_register()
            elif function == 7:
                self.parse_read_exception_status()
            elif function == 8:
                self.parse_diagnostics()
            elif function == 11:
                self.parse_get_comm_event_counter()
            elif function == 12:
                self.parse_get_comm_event_log()
            elif function == 15 or function == 16:
                self.parse_write_multiple()
            elif function == 17:
                self.parse_report_server_id()
            elif function == 22:
                self.parse_mask_write_register()
            elif function in {21, 21, 24, 43}:
                self.parse_not_implemented()
            elif function > 0x80:
                self.parse_error()
            else:
                self.puti(1, 'error',
                          'Unknown function: {}'.format(data[1].data))
                self.putl('error', 'Unknown function')

            # If the message gets here without raising an exception, the
            # message goes on longer than it should.
            self.putl('error', 'Message too long')

        except No_more_data:
            # Just a message saying we don't need to parse anymore this round.
            pass

    def parse_read_bits(self):
        self.mimumum_length = 5

        data = self.data
        function = data[1].data

        if function == 1:
            self.puti(1, 'function', 'Function 1: Read Coils')
        else:
            self.puti(1, 'function', 'Function 2: Read Discrete Inputs')

        bytecount = self.data[2].data
        self.minimum_length = 5 + bytecount # 3 before data, 2 CRC.
        self.puti(2, 'length', 'Byte count: {}'.format(bytecount))

        # From here on out, we expect registers on 3 and 4, 5 and 6 etc.
        # So registers never start when the length is even.
        self.putl('data', '{:08b}', bytecount + 2)
        self.check_crc(bytecount + 4)

    def parse_read_registers(self):
        self.mimumum_length = 5

        data = self.data

        function = data[1].data
        if function == 3:
            self.puti(1, 'function', 'Function 3: Read Holding Registers')
        elif function == 4:
            self.puti(1, 'function', 'Function 4: Read Input Registers')
        elif function == 23:
            self.puti(1, 'function', 'Function 23: Read/Write Multiple Registers')

        bytecount = self.data[2].data
        self.minimum_length = 5 + bytecount # 3 before data, 2 CRC.
        if bytecount % 2 == 0:
            self.puti(2, 'length', 'Byte count: {}'.format(bytecount))
        else:
            self.puti(2, 'error',
                'Error: Odd byte count ({})'.format(bytecount))

        # From here on out, we expect registers on 3 and 4, 5 and 6 etc.
        # So registers never start when the length is even.
        if len(data) % 2 == 1:
            register_value = self.half_word(-2)
            self.putl('data', '0x{0:04X} / {0}'.format(register_value),
                      bytecount + 2)
        else:
            raise No_more_data

        self.check_crc(bytecount + 4)

    def parse_read_exception_status(self):
        self.mimumum_length = 5

        self.puti(1, 'function', 'Function 7: Read Exception Status')
        exception_status = self.data[2].data
        self.puti(2, 'data',
                  'Exception status: {:08b}'.format(exception_status))
        self.check_crc(4)

    def parse_get_comm_event_counter(self):
        self.mimumum_length = 8

        self.puti(1, 'function', 'Function 11: Get Comm Event Counter')

        status = self.half_word(2)
        if status == 0x0000:
            self.puti(3, 'data', 'Status: not busy')
        elif status == 0xFFFF:
            self.puti(3, 'data', 'Status: busy')
        else:
            self.puti(3, 'error', 'Bad status: 0x{:04X}'.format(status))

        count = self.half_word(4)
        self.puti(5, 'data', 'Event Count: {}'.format(count))
        self.check_crc(7)

    def parse_get_comm_event_log(self):
        self.mimumum_length = 11
        self.puti(1, 'function', 'Function 12: Get Comm Event Log')

        data = self.data

        bytecount = data[2].data
        self.puti(2, 'length', 'Bytecount: {}'.format(bytecount))
        # The bytecount is the length of everything except the slaveID,
        # function code, bytecount and CRC.
        self.mimumum_length = 5 + bytecount

        status = self.half_word(3)
        if status == 0x0000:
            self.puti(4, 'data', 'Status: not busy')
        elif status == 0xFFFF:
            self.puti(4, 'data', 'Status: busy')
        else:
            self.puti(4, 'error', 'Bad status: 0x{:04X}'.format(status))

        event_count = self.half_word(5)
        self.puti(6, 'data', 'Event Count: {}'.format(event_count))

        message_count = self.half_word(7)
        self.puti(8, 'data', 'Message Count: {}'.format(message_count))

        self.putl('data', 'Event: 0x{:02X}'.format(data[-1].data),
                  bytecount + 2)

        self.check_crc(bytecount + 4)

    def parse_write_multiple(self):
        '''Function 15 and 16 are almost the same, so we can parse them both
        using one function.'''
        self.mimumum_length = 8

        function = self.data[1].data
        if function == 15:
            data_unit = 'Coils'
            max_outputs = 0x07B0
            long_address_offset = 10001
        elif function == 16:
            data_unit = 'Registers'
            max_outputs = 0x007B
            long_address_offset = 30001

        self.puti(1, 'function',
            'Function {}: Write Multiple {}'.format(function, data_unit))

        starting_address = self.half_word(2)
        # Some instruction manuals use a long form name for addresses, this is
        # listed here for convienience.
        address_name = long_address_offset + starting_address
        self.puti(3, 'address',
            'Start at address 0x{:X} / {:d}'.format(starting_address,
                                                    address_name))

        quantity_of_outputs = self.half_word(4)
        if quantity_of_outputs <= max_outputs:
            self.puti(5, 'data',
                'Write {} {}'.format(quantity_of_outputs, data_unit))
        else:
            self.puti(5, 'error',
                'Bad value: {} {}. Max is {}'.format(quantity_of_outputs,
                                                     data_unit, max_outputs))

        self.check_crc(7)

    def parse_report_server_id(self):
        # Buildup of this function:
        # 1 byte serverID
        # 1 byte function (17)
        # 1 byte bytecount
        # 1 byte serverID (counts for bytecount)
        # 1 byte Run Indicator Status (counts for bytecount)
        # bytecount - 2 bytes of device specific data (counts for bytecount)
        # 2 bytes of CRC
        self.mimumum_length = 7
        data = self.data
        self.puti(1, 'function', 'Function 17: Report Server ID')

        bytecount = data[2].data
        self.puti(2, 'length', 'Data is {} bytes long'.format(bytecount))

        self.puti(3, 'data', 'serverID: {}'.format(data[3].data))

        run_indicator_status = data[4].data
        if run_indicator_status == 0x00:
            self.puti(4, 'data', 'Run Indicator status: Off')
        elif run_indicator_status == 0xFF:
            self.puti(4, 'data', 'Run Indicator status: On')
        else:
            self.puti(4, 'error',
                'Bad Run Indicator status: 0x{:X}'.format(run_indicator_status))

        self.putl('data', 'Device specific data: {}, "{}"'.format(data[-1].data,
                  chr(data[-1].data)), 2 + bytecount)

        self.check_crc(4 + bytecount)

    def parse_error(self):
        '''Parse a Modbus error message.'''
        self.mimumum_length = 5
        # The function code of an error is always 0x80 above the function call
        # that caused it.
        functioncode = self.data[1].data - 0x80

        functions = {
            1: 'Read Coils',
            2: 'Read Discrete Inputs',
            3: 'Read Holding Registers',
            4: 'Read Input Registers',
            5: 'Write Single Coil',
            6: 'Write Single Register',
            7: 'Read Exception Status',
            8: 'Diagnostic',
            11: 'Get Com Event Counter',
            12: 'Get Com Event Log',
            15: 'Write Multiple Coils',
            16: 'Write Multiple Registers',
            17: 'Report Slave ID',
            20: 'Read File Record',
            21: 'Write File Record',
            22: 'Mask Write Register',
            23: 'Read/Write Multiple Registers',
            24: 'Read FIFO Queue',
            43: 'Read Device Identification/Encapsulated Interface Transport',
        }
        functionname = '{}: {}'.format(functioncode,
            functions.get(functioncode, 'Unknown function'))
        self.puti(1, 'function',
                  'Error for function {}'.format(functionname))

        error = self.data[2].data
        errorcodes = {
            1: 'Illegal Function',
            2: 'Illegal Data Address',
            3: 'Illegal Data Value',
            4: 'Slave Device Failure',
            5: 'Acknowledge',
            6: 'Slave Device Busy',
            8: 'Memory Parity Error',
            10: 'Gateway Path Unavailable',
            11: 'Gateway Target Device failed to respond',
        }
        errorname = '{}: {}'.format(error, errorcodes.get(error, 'Unknown'))
        self.puti(2, 'data', 'Error {}'.format(errorname))
        self.check_crc(4)

class Modbus_ADU_CS(Modbus_ADU):
    '''CS stands for Client -> Server.'''
    def parse(self):
        '''Select which specific Modbus function we should parse.'''
        data = self.data

        # This try-catch is being used as flow control.
        try:
            server_id = data[0].data
            message = ''
            if server_id == 0:
                message = 'Broadcast message'
            elif 1 <= server_id <= 247:
                message = 'Slave ID: {}'.format(server_id)
            elif 248 <= server_id <= 255:
                message = 'Slave ID: {} (reserved address)'.format(server_id)
            self.puti(0, 'server-id', message)

            function = data[1].data
            if function >= 1 and function <= 4:
                self.parse_read_data_command()
            if function == 5:
                self.parse_write_single_coil()
            if function == 6:
                self.parse_write_single_register()
            if function in {7, 11, 12, 17}:
                self.parse_single_byte_request()
            elif function == 8:
                self.parse_diagnostics()
            if function in {15, 16}:
                self.parse_write_multiple()
            elif function == 22:
                self.parse_mask_write_register()
            elif function == 23:
                self.parse_read_write_registers()
            elif function in {21, 21, 24, 43}:
                self.parse_not_implemented()
            else:
                self.puti(1, 'error',
                          'Unknown function: {}'.format(data[1].data))
                self.putl('error', 'Unknown function')

            # If the message gets here without raising an exception, the
            # message goes on longer than it should.
            self.putl('error', 'Message too long')

        except No_more_data:
            # Just a message saying we don't need to parse anymore this round.
            pass

    def parse_read_data_command(self):
        '''Interpret a command to read x units of data starting at address, ie
        functions 1, 2, 3 and 4, and write the result to the annotations.'''
        data = self.data
        self.minimum_length = 8

        function = data[1].data
        functionname = {1: 'Read Coils',
                        2: 'Read Discrete Inputs',
                        3: 'Read Holding Registers',
                        4: 'Read Input Registers',
                        }[function]

        self.puti(1, 'function',
                  'Function {}: {}'.format(function, functionname))

        starting_address = self.half_word(2)
        # Some instruction manuals use a long form name for addresses, this is
        # listed here for convienience.
        # Example: holding register 60 becomes 30061.
        address_name = 10000 * function + 1 + starting_address
        self.puti(3, 'address',
            'Start at address 0x{:X} / {:d}'.format(starting_address,
                                                    address_name))

        self.puti(5, 'length',
                  'Read {:d} units of data'.format(self.half_word(4)))
        self.check_crc(7)

    def parse_single_byte_request(self):
        '''Some Modbus functions have no arguments, this parses those.'''
        function = self.data[1].data
        function_name = {7: 'Read Exception Status',
                         11: 'Get Comm Event Counter',
                         12: 'Get Comm Event Log',
                         17: 'Report Slave ID',
                         }[function]
        self.puti(1, 'function',
                  'Function {}: {}'.format(function, function_name))

        self.check_crc(3)

    def parse_write_multiple(self):
        '''Function 15 and 16 are almost the same, so we can parse them both
        using one function.'''
        self.mimumum_length = 9

        function = self.data[1].data
        if function == 15:
            data_unit = 'Coils'
            max_outputs = 0x07B0
            ratio_bytes_data = 1/8
            long_address_offset = 10001
        elif function == 16:
            data_unit = 'Registers'
            max_outputs = 0x007B
            ratio_bytes_data = 2
            long_address_offset = 30001

        self.puti(1, 'function',
            'Function {}: Write Multiple {}'.format(function, data_unit))

        starting_address = self.half_word(2)
        # Some instruction manuals use a long form name for addresses, this is
        # listed here for convienience.
        address_name = long_address_offset + starting_address
        self.puti(3, 'address',
            'Start at address 0x{:X} / {:d}'.format(starting_address,
                                                    address_name))

        quantity_of_outputs = self.half_word(4)
        if quantity_of_outputs <= max_outputs:
            self.puti(5, 'length',
                'Write {} {}'.format(quantity_of_outputs, data_unit))
        else:
            self.puti(5, 'error',
                'Bad value: {} {}. Max is {}'.format(quantity_of_outputs,
                                                     data_unit, max_outputs))
        proper_bytecount = ceil(quantity_of_outputs * ratio_bytes_data)

        bytecount = self.data[6].data
        if bytecount == proper_bytecount:
            self.puti(6, 'length', 'Byte count: {}'.format(bytecount))
        else:
            self.puti(6, 'error',
                'Bad byte count, is {}, should be {}'.format(bytecount,
                                                             proper_bytecount))
        self.mimumum_length = bytecount + 9

        self.putl('data', 'Value 0x{:X}', 6 + bytecount)

        self.check_crc(bytecount + 8)

    def parse_read_file_record(self):
        self.puti(1, 'function', 'Function 20: Read file records')

        data = self.data

        bytecount = data[2].data

        self.minimum_length = 5 + bytecount
        # 1 for serverID, 1 for function, 1 for bytecount, 2 for CRC.

        if 0x07 <= bytecount <= 0xF5:
            self.puti(2, 'length', 'Request is {} bytes long'.format(bytecount))
        else:
            self.puti(2, 'error',
                'Request claims to be {} bytes long, legal values are between'
                ' 7 and 247'.format(bytecount))

        current_byte = len(data) - 1
        # Function 20 is a number of sub-requests, the first starting at 3,
        # the total length of the sub-requests is bytecount.
        if current_byte <= bytecount + 2:
            step = (current_byte - 3) % 7
            if step == 0:
                if data[current_byte].data == 6:
                    self.puti(current_byte, 'data', 'Start sub-request')
                else:
                    self.puti(current_byte, 'error',
                        'First byte of subrequest should be 0x06')
            elif step == 1:
                raise No_more_data
            elif step == 2:
                file_number = self.half_word(current_byte - 1)
                self.puti(current_byte, 'data',
                          'Read File number {}'.format(file_number))
            elif step == 3:
                raise No_more_data
            elif step == 4:
                record_number = self.half_word(current_byte - 1)
                self.puti(current_byte, 'address',
                    'Read from record number {}'.format(record_number))
                # TODO: Check if within range.
            elif step == 5:
                raise No_more_data
            elif step == 6:
                records_to_read = self.half_word(current_byte - 1)
                self.puti(current_byte, 'length',
                    'Read {} records'.format(records_to_read))
        self.check_crc(4 + bytecount)

    def parse_read_write_registers(self):
        '''Parse function 23: Read/Write multiple registers.'''
        self.minimum_length = 13

        self.puti(1, 'function', 'Function 23: Read/Write Multiple Registers')

        starting_address = self.half_word(2)
        # Some instruction manuals use a long form name for addresses, this is
        # listed here for convienience.
        # Example: holding register 60 becomes 30061.
        address_name = 30001 + starting_address
        self.puti(3, 'address',
            'Read starting at address 0x{:X} / {:d}'.format(starting_address,
                                                            address_name))

        self.puti(5, 'length', 'Read {:d} units of data'.format(self.half_word(4)))

        starting_address = self.half_word(6)
        self.puti(7, 'address',
            'Write starting at address 0x{:X} / {:d}'.format(starting_address,
                                                             address_name))

        quantity_of_outputs = self.half_word(8)
        self.puti(9, 'length',
                           'Write {} registers'.format(quantity_of_outputs))
        proper_bytecount = quantity_of_outputs * 2

        bytecount = self.data[10].data
        if bytecount == proper_bytecount:
            self.puti(10, 'length', 'Byte count: {}'.format(bytecount))
        else:
            self.puti(10, 'error',
                'Bad byte count, is {}, should be {}'.format(bytecount,
                                                             proper_bytecount))
        self.mimumum_length = bytecount + 13

        self.putl('data', 'Data, value 0x{:02X}', 10 + bytecount)

        self.check_crc(bytecount + 12)

class Decoder(srd.Decoder):
    api_version = 3
    id = 'modbus'
    name = 'Modbus'
    longname = 'Modbus RTU over RS232/RS485'
    desc = 'Modbus RTU protocol for industrial applications.'
    license = 'gplv3+'
    inputs = ['uart']
    outputs = ['modbus']
    tags = ['Embedded/industrial']
    annotations = (
        ('sc-server-id', 'SC server ID'),
        ('sc-function', 'SC function'),
        ('sc-crc', 'SC CRC'),
        ('sc-address', 'SC address'),
        ('sc-data', 'SC data'),
        ('sc-length', 'SC length'),
        ('sc-error', 'SC error'),
        ('cs-server-id', 'CS server ID'),
        ('cs-function', 'CS function'),
        ('cs-crc', 'CS CRC'),
        ('cs-address', 'CS address'),
        ('cs-data', 'CS data'),
        ('cs-length', 'CS length'),
        ('cs-error', 'CS error'),
        ('error-indication', 'Error indication'),
    )
    annotation_rows = (
        ('sc', 'Server->client', (0, 1, 2, 3, 4, 5, 6)),
        ('cs', 'Client->server', (7, 8, 9, 10, 11, 12, 13)),
        ('error-indicators', 'Errors in frame', (14,)),
    )
    options = (
        {'id': 'scchannel', 'desc': 'Server -> client channel',
            'default': rxtx_channels[0], 'values': rxtx_channels},
        {'id': 'cschannel', 'desc': 'Client -> server channel',
            'default': rxtx_channels[1], 'values': rxtx_channels},
        {'id': 'framegap', 'desc': 'Inter-frame bit gap', 'default': 28},
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.ADUSc = None # Start off with empty slave -> client ADU.
        self.ADUCs = None # Start off with empty client -> slave ADU.

        # The reason we have both (despite not supporting full duplex comms) is
        # because we want to be able to decode the message as both client ->
        # server and server -> client, and let the user see which of the two
        # the ADU was.

        self.bitlength = None # We will later test how long a bit is.

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def puta(self, start, end, ann_str, message):
        '''Put an annotation from start to end, with ann as a
        string. This means you don't have to know the ann's
        number to write annotations to it.'''
        ann = [s[0] for s in self.annotations].index(ann_str)
        self.put(start, end, self.out_ann, [ann, [message]])

    def decode_adu(self, ss, es, data, direction):
        '''Decode the next byte or bit (depending on type) in the ADU.
        ss: Start time of the data
        es: End time of the data
        data: Data as passed from the UART decoder
        direction: Is this data for the Cs (client -> server) or Sc (server ->
                   client) being decoded right now?'''
        ptype, rxtx, pdata = data

        # We don't have a nice way to get the baud rate from UART, so we have
        # to figure out how long a bit lasts. We do this by looking at the
        # length of (probably) the startbit.
        if self.bitlength is None:
            if ptype == 'STARTBIT' or ptype == 'STOPBIT':
                self.bitlength = es - ss
            else:
                # If we don't know the bitlength yet, we can't start decoding.
                return

        # Select the ADU, create the ADU if needed.
        # We set ADU.startNewFrame = True when we know the old one is over.
        if direction == 'Sc':
            if (self.ADUSc is None) or self.ADUSc.startNewFrame:
                self.ADUSc = Modbus_ADU_SC(self, ss, TX, 'sc-')
            ADU = self.ADUSc
        if direction == 'Cs':
            if self.ADUCs is None or self.ADUCs.startNewFrame:
                self.ADUCs = Modbus_ADU_CS(self, ss, TX, 'cs-')
            ADU = self.ADUCs

        # We need to determine if the last ADU is over.
        # According to the Modbus spec, there should be 3.5 characters worth of
        # space between each message. But if within a message there is a length
        # of more than 1.5 character, that's an error. For our purposes
        # somewhere between seems fine.
        # A character is 11 bits long, so (3.5 + 1.5)/2 * 11 ~= 28
        # TODO: Display error for too short or too long.
        if (ss - ADU.last_read) <= self.bitlength * self.options['framegap']:
            ADU.add_data(ss, es, data)
        else:
            # It's been too long since the last part of the ADU!
            # If there is any data in the ADU we need to show it to the user
            if len(ADU.data) > 0:
                # Extend errors for 3 bits after last byte, we can guarantee
                # space.
                ADU.close(ADU.data[-1].end + self.bitlength * 3)

            ADU.startNewFrame = True
            # Restart this function, it will make a new ADU for us.
            self.decode_adu(ss, es, data, direction)

    def decode(self, ss, es, data):
        ptype, rxtx, pdata = data

        # Ignore unknown/unsupported ptypes.
        if ptype not in ('STARTBIT', 'DATA', 'STOPBIT'):
            return

        # Decide what ADU(s) we need this packet to go to.
        # Note that it's possible to go to both ADUs.
        if rxtx_channels[rxtx] == self.options['scchannel']:
            self.decode_adu(ss, es, data, 'Sc')
        if rxtx_channels[rxtx] == self.options['cschannel']:
            self.decode_adu(ss, es, data, 'Cs')
