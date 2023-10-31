from .monitor import ProductMonitor


def start_farfetch_monitor():
    ProductMonitor(source_type=1).start()


def start_intramirror_monitor():
    ProductMonitor(source_type=3).start()
