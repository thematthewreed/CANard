import json
from .. import can, messaging

class JsonDbParser():
    def parse(self, filename):
        with open(filename, 'r') as f:
            db = json.load(f)

            # create a message database
            msgdb = messaging.MessageDatabase()
            for msg in db['messages']:
                # create a message
                m = messaging.Message(msg['name'], int(msg['id'], 0))

                # iterate over signals
                for start_bit, sig in msg['signals'].items():
                    # create a signal
                    s = messaging.Signal(sig['name'], sig['bit_length'])

                    # parse offset and factor if set
                    if 'offset' in sig:
                        s.offset = int(sig['offset'])
                    if 'factor' in sig:
                        s.factor = sig['factor']

                    # parse unit if set
                    if 'unit' in sig:
                        s.unit = sig['unit']

                    # add this signal to the message
                    m.add_signal(s, int(start_bit))

                # add this message to the database
                msgdb.add_message(m)

        return msgdb
