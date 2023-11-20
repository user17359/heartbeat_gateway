class DiaryEntry:
    def __init__(self, label, hour, minute, description):
        self.label = label
        self.hour = hour
        self.minute = minute
        self.description = description

    def to_json(self):
        return {
            'label': self.label,
            'hour': self.hour,
            'minute': self.minute,
            'description': self.description
        }