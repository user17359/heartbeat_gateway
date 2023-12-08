import asyncio

from bluez_peripheral.advert import Advertisement


class Advertiser:
    is_advertisement_running = False
    name = "Heartbeat 2809"
    serviceUUIDs = ["180D"]
    appearance = 0x008D
    adv_time = 60

    def __init__(self, bt_led, bus, adapter, scheduler):
        self.bt_led = bt_led
        self.bus = bus
        self.adapter = adapter
        self.scheduler = scheduler

    def advertisement_end(self, saved_status):
        self.is_advertisement_running = False
        if self.bt_led.value == 1:
            pass
        if saved_status == 1:
            self.bt_led.on()
        else:
            self.bt_led.off()

    def setup_connection(self):
        if not self.is_advertisement_running:
            status = self.bt_led.value

            self.bt_led.blink()
            self.is_advertisement_running = True
            self.scheduler.enter(delay=self.adv_time, priority=1, action=self.advertisement_end, argument=(status,))
            asyncio.run(self.setup_connection_async())
        else:
            print("[red]Advertisement already running![/red]")

    async def setup_connection_async(self):
        print("Start of advertisement :loudspeaker:")
        advert = Advertisement(self.name, self.serviceUUIDs, self.appearance, self.adv_time)
        await advert.register(self.bus, self.adapter)