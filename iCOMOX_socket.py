import messages_utils
import iCOMOX_messages

class iCOMOX_socket():
    def __init__(self, sock, remote_address, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.socket = sock
        self.remote_address = remote_address
        self.UniqueID = None
        self.Name = None
        self.board_type = None
        self.Hello = None
        self.Reports = [None] * 256 #(iCOMOX_messages.cCOMOX_SENSOR_COUNT + 2)
        self.KnowtionReport = None
        self.accumulated_msg = bytearray()
        self.receive_buffer = bytearray()
        self.transmit_buffer = bytearray()
        self.ConnectionTime = None
        # self.BG96_Encoding = False
        # self.prev_escaped_char = False

    def __del__(self):
        self.accumulated_msg = None
        self.receive_buffer = None
        self.transmit_buffer = None
        del self.socket
