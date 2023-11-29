from datetime import datetime


class TimestampConverter:
    start_utf_timestamp = -1
    start_movesense_timestamp = -1

    def convert_timestamp(self, movesense_timestamp):
        if movesense_timestamp == -1:
            self.start_movesense_timestamp = -1
            self.start_utf_timestamp = -1
            return -1
        else:
            if self.start_movesense_timestamp == -1:
                now = datetime.now()
                # * 1000 to account for timestamp being in milliseconds
                self.start_utf_timestamp = now.timestamp() * 1000
                self.start_movesense_timestamp = movesense_timestamp
                return int(self.start_utf_timestamp)
            else:
                return int(self.start_utf_timestamp + (movesense_timestamp - self.start_movesense_timestamp))

