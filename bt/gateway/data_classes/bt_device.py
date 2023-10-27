class BtDevice:
    def __init__(self, name, mac):
        self.name = name
        self.mac = mac

    def to_json(self):
        return {
            'name': self.name,
            'mac': self.mac
        }
