""" messaging.py

Defines messages and message interfaces for storing and retrieving CAN frames

"""

from . import can
import math

class MessageDatabase:
    """ Database of CAN messages """
    
    def __init__(self):
        # message that belong to this database
        self._messages = []
    
    def __getattr__(self, name):
        return self.lookup_message(name)

    def add_message(self, message):
        assert isinstance(message, Message), 'invalid message'
        if message in self._messages:
            raise ValueError('Message %s already in database' % message)
        else:
            self._messages.append(message)

    def remove_message(self, message):
        assert isinstance(Message, message), 'invalid message'
        try:
            self._messages.remove(message)
        except ValueError:
            raise ValueError('Message %s is not in database' % message)
    
    def lookup_message(self, name):
        for message in self._messages:
            if message.name == name:
                return message
            
    def decode(self, frame):
        assert isinstance(frame, can.Frame), 'invalid frame'
        for message in self._messages:
            if message.id == frame.id:
                return message.decode(frame)

    def __str__(self):
        s = "MessageDatabase:\n"
        for message in self._messages:
            s = s + message.__str__()
        return s

class Message(object):
    
    def __getattr__(self, name):
        return self.lookup_signal(name)

    def __init__(self, name, id):
        self.name = name
        self.id = id
        # signals that belong to this message, indexed by start bit
        self._signals = {}

    def add_signal(self, signal, start_bit):
        assert isinstance(signal, Signal), 'invalid signal'
        assert isinstance(start_bit, int) and start_bit < 63, 'invalid start bit'
        self._signals[start_bit] = signal

    def remove_signal(self, signal):
        pass
    
    def lookup_signal(self, name):
        for start_bit, signal in self._signals.items():
            if signal.name == name:
                return signal

    def decode(self, frame):
        assert isinstance(frame, can.Frame), 'invalid frame'
        assert frame.id == self.id, 'frame id does not match message id'

        # combine 8 data bytes into single value
        frame_value = 0
        for i in range(0, frame.dlc):
            if frame.data[i] != None:
                frame_value = frame_value + (frame.data[i] << (8 * i))

        result_signals = []

        # iterate over signals
        for start_bit, signal in self._signals.items():

            # find the last bit of the singal
            end_bit = signal.bit_length + start_bit

            # compute the mask
            mask = 0
            for j in range(start_bit, end_bit):
                mask = mask + 2**j

            # apply the mask, then downshift
            value = (frame_value & mask) >> start_bit
            # pass the maksed value to the signal
            signal.raw_value = value

            result_signals.append(signal)

        return self
    
    def encode(self):
        #start with a single value before breaking up into bytes
        frame_value = 0
        # iterate over signals
        for start_bit, signal in sorted(self._signals.items()):
            #print("bit: " + str(start_bit))

            value = signal.raw_value
            assert (value < pow(2, signal.bit_length)), 'signal value is too large'
            assert value >= 0, 'signal value is less than 0'
            
            frame_value += value << start_bit

            # find the last bit of the singal
            start_bit = signal.bit_length + start_bit
            
        frame = can.Frame(self.id)
        #print("bits: " + str(start_bit))
        frame.dlc = math.ceil(start_bit / 8)
        #print("dlc: " + str(frame.dlc))
        data = []
        for i in range(0, frame.dlc):
            data.append((frame_value >> (i * 8)) & 0xff)
            #print("data " + str(i) + ": " + str((frame_value >> (i * 8)) & 0xff))

        ##print("end")
        frame.data = data
        return frame

    def __str__(self):
        s = "Message: %s, ID: 0x%X\n" % (self.name, self.id)
        for start_bit, signal in self._signals.items():
            s = s + "\t" + signal.__str__() + "\n"
        return s

class Signal:
    """ Represents a data value

    Attributes:
        name (str): signal name
        bit_length (int): length of raw signal data in bits
        factor (float): factor used to convert raw value to engineering units
        offset (int): offeset used to convert raw value to engineering units
        unit (str): enineering units used for signal value
        value (float): signal value in engineering units
        raw_value (int): raw signal value without any conversions
    """
    def __init__(self, name, bit_length, factor=1, offset=0, unit=""):
        self.name = name
        self.bit_length = bit_length
        self.factor = factor
        self.offset = offset
        self.unit = unit
        self._value = 0

    @property
    def value(self):
        # convert from raw value to engineering units
        return ((self._value * self.factor) - self.offset)
    
    @value.setter
    def value(self, value):
        # convert from engineering units to raw value
        self._value = ((value - self.offset) / self.factor)
        return self
    
    @property
    def raw_value(self):
        # get raw value directly without any conversions
        return int(self._value)
    
    @raw_value.setter
    def raw_value(self, value):
        # set raw value directly without any conversions
        self._value = value
        return self

    def __str__(self):
        s = "Signal: %s\tValue = %d" % (self.name, self.value)
        return s
