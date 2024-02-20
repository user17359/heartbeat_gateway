class BtDevice:
    def __init__(self, name, mac, details):
        self.name = name
        self.mac = mac
        self.details = details

    def to_json(self):
        return {
            'name': self.name,
            'mac': self.mac,
            'details': self.details
        }
