cESCAPE_CHAR        = 255

cPREV_ESC_CHAR_00   = 1
cPREV_ESC_CHAR_08   = 2
cPREV_ESC_CHAR_1A   = 3
cPREV_ESC_CHAR_1B   = 4
cPREV_ESC_CHAR_FF   = 5

# [DecodeOk, prev_escaped_char, data_out] = decode(data_in, prev_escaped_char)
# IN PARAMETERS:
# data_in - bytearray with the encoded data,
# prev_escaped_char - if the last data_in in previous call to decode() has ended with the cESCAPE_CHAR
# OUT PARAMETERS:
# DecodeOk - is the decoding succeeded
# prev_escaped_char - did the last byte in data_in is cESCAPE_CHAR (should be transferred to the next call to decode())
# data_out - bytearray which contains the decoded array
def decode(data_in, prev_escaped_char):
    #   0x00 -> 0xFF 0x01
    #   0x08 -> 0xFF 0x02
    #   0x1A -> 0xFF 0x03
    #   0x1B -> 0xFF 0x04
    #   0xFF -> 0xFF 0x05
    data_out = bytearray()
    for i in range(0, len(data_in)):
        if prev_escaped_char:
            if data_in[i] == cPREV_ESC_CHAR_00:
                data_out += b"\x00"
            elif data_in[i] == cPREV_ESC_CHAR_08:
                data_out += b"\x08"
            elif data_in[i] == cPREV_ESC_CHAR_1A:
                data_out += b"\x1A"
            elif data_in[i] == cPREV_ESC_CHAR_1B:
                data_out += b"\x1B"
            elif data_in[i] == cPREV_ESC_CHAR_FF:
                data_out += b"\xFF"
            else:
                return False, False, data_out  # [ decode fail = False, prev_escaped_char = False ]
            prev_escaped_char = False
        else:
            if data_in[i] == cESCAPE_CHAR:
                prev_escaped_char = True
            elif (data_in[i] == 0) or (data_in[i] == 8) or (data_in[i] == 26) or (data_in[i] == 27):
                return False, False, data_out
            else:
                data_out += bytearray([data_in[i]])
    return True, prev_escaped_char, data_out

# [prev_escaped_char, data_out] = encode(data_in, prev_escaped_char)
# IN PARAMETERS:
# data_in - bytearray with the non-encoded data,
# OUT PARAMETERS:
# data_out - bytearray which contains the encoded array
def encode(data_in):
    #   0x00 -> 0xFF 0x01
    #   0x08 -> 0xFF 0x02
    #   0x1A -> 0xFF 0x03
    #   0x1B -> 0xFF 0x04
    #   0xFF -> 0xFF 0x05
    data_out = bytearray()
    for i in range(0, len(data_in)):
        if data_in[i] == 0:
            data_out += b"\xFF\x01"
        elif data_in[i] == 8:
            data_out += b"\xFF\x02"
        elif data_in[i] == 26:
            data_out += b"\xFF\x03"
        elif data_in[i] == 27:
            data_out += b"\xFF\x04"
        elif data_in[i] == 255:
            data_out += b"\xFF\x05"
        else:
            data_out += bytearray([data_in[i]])
    return data_out
