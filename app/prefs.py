'''
Created on Apr 15, 2015

@author: bgrivna
'''

import logging
import os
import pickle

logger = logging.getLogger(__name__)

class Prefs:
    def __init__(self, prefPath):
        self.prefPath = prefPath

        self.prefmap = {}
        self.read()
    
    def write(self):
        with open(self.prefPath, 'wb') as pf:
            pickle.dump(self.prefmap, pf)
            pf.close()
            logger.info("saved preferences: " + str(self.prefmap))
    
    def read(self):
        if os.path.exists(self.prefPath):
            pf = open(self.prefPath, 'rb')
            self.prefmap = pickle.load(pf)
            pf.close()
            logger.info("loaded prefs: " + str(self.prefmap))
        else:
            logger.info("no prefs found at " + self.prefPath)
            
    def get(self, key, default=""):
        return self.prefmap[key] if key in self.prefmap else default

    def contains(self, key):
        return key in self.prefmap
    
    def set(self, key, value):
        self.prefmap[key] = value

    def getAll(self):
        return self.prefmap.copy()

    def setAll(self, prefMap):
        self.prefmap = prefMap
