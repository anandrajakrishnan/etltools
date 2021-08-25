'''
Created on Oct 8, 2020

@author: ANAND_RA_Temp
'''
from abc import ABC,abstractmethod
class Inbound(ABC):
    @abstractmethod
    def checkPrevJobStatus(self):
        '''
        This method is to check the JMAN status of the last executed job
        '''
        pass
    @abstractmethod
    def unzipIncoming(self):
        '''
        To unzip source (DB connection /file size etc.) and confirm that
        the source is good to provide data for processing
        '''
        pass
    @abstractmethod
    def processData(self):
        '''
        load the data into target
        '''
        pass
    @abstractmethod
    def checkFeedcount(self):
        '''
        check the failed loads in the JMAN.FEEDCOUNT table (Is this required in Interface?)
        '''
        pass
    @abstractmethod
    def updJobRunDetails(self):
        '''
        update JMAN after successful loading of data
        '''
        pass
