from abc import ABC, abstractmethod

class IFormScrapper(ABC):

 @abstractmethod
 def fill_out_form(self,wait,driver,case_information,actions):
     pass