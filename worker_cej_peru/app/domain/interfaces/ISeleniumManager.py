from abc import ABC, abstractmethod


class ISeleniumManager(ABC):

    # @abstractmethod
    # async def start_login(self):
    #     pass

    @abstractmethod
    def init(self):
        pass

    @abstractmethod
    def get_driver(self):
      pass

    def close(self):
       pass