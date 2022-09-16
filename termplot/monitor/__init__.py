from abc import ABC


class AbstractMonitor(ABC):
    def should_refresh(self) -> bool:
        return False

    def stop(self) -> None:
        pass

    def set_should_refresh(self):
        pass

    def reset_condition(self):
        pass

    def wait_till_new_modification(self):
        pass

    def get_latest(self):
        raise NotImplementedError()
