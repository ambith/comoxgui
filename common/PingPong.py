# class ClassPingPong
# Purpose: Implementing mechanism for a single ping pong buffer
class ClassPingPong:
    def __init__(self):
        self.clear()

    def clear(self):
        self.Buffers = [bytearray(), bytearray()]   # messages that arrive/processed
        self.BufferPopulated = [False, False]       # False = Buffers[] is empty or already have been processed
                                                    # True = Buffers[] is populated and not have been processed yet
        self.SenderBufIndex = 0  #
        self.ReceiverBufIndex = 0  #

    def try_push_msg(self, msg):
        # Here we push the incoming messages from the class_iCOMOX_Communication thread to a ping pong buffer, if possible
        if not self.BufferPopulated[self.SenderBufIndex]:
            self.Buffers[self.SenderBufIndex] = msg
            self.BufferPopulated[self.SenderBufIndex] = True
            self.SenderBufIndex = 1 - self.SenderBufIndex
            return True  # Succeeded to push a message
        else:
            return False  # No message can be pushed

    def try_pop_msg(self):
        if self.BufferPopulated[self.ReceiverBufIndex]:
            msg = self.Buffers[self.ReceiverBufIndex]
            # self.process_incoming_msg(msg)
            self.BufferPopulated[self.ReceiverBufIndex] = False
            self.ReceiverBufIndex = 1 - self.ReceiverBufIndex
            return msg  # Succeeded to pop a message
        else:
            return None  # No message can be pop


class ClassPingPongArr:
    def __init__(self, count):
        self.__PingPongArr__ = []
        for i in range(0, count):
            self.__PingPongArr__.append(ClassPingPong())

    def assert_index(self, index):
        assert ((index >= 0) and (index < len(self.__PingPongArr__)))

    def clear(self, index):
        self.assert_index(index=index)
        self.__PingPongArr__[index].clear()

    def clear_all(self):
        for PingPong in self.__PingPongArr__:
            PingPong.clear()

    def try_push_msg(self, index, msg):
        self.assert_index(index=index)
        return self.__PingPongArr__[index].try_push_msg(msg=msg)

    def try_pop_msg(self, index):
        self.assert_index(index=index)
        return self.__PingPongArr__[index].try_pop_msg()

    def count(self):
        return len(self.__PingPongArr__)
