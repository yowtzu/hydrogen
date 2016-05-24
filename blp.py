import blpapi
import pandas as pd
import numpy as np
import itertools
import yaml
import re
import os
from datetime import datetime

class BLPRequestError(Exception):
    """A generic exception raised when there is a Bloomberg API request."""
    def __init__ (self, value):
        self.value = value
        
    def __str__ (self):
        return repr(self.value)

class BLPService:
    """ A wrapper for the Bloomberg API that returns DataFrames.  This class
        manages a //BLP/refdata service and therefore does not handle event
        subscriptions.
    
        All calls are blocking and responses are parsed and returned as 
        DataFrames where appropriate. 
    
        A RequestError is raised when an invalid security is queried.  Invalid
        fields will fail silently and may result in an empty DataFrame.
    """ 
    def __init__ (self, host='localhost', port=8194):
        self._connected = False
        self.host = host
        self.port = port
        self._connect()
        
    def _connect(self):
        if not self._connected:
            sessionOptions = blpapi.SessionOptions()
            sessionOptions.setServerHost(self.host)
            sessionOptions.setServerPort(self.port)
            self.session = blpapi.Session(sessionOptions)
            self.session.start()
            self.session.openService('//BLP/refdata')
            self.refDataService = self.session.getService('//BLP/refdata')
            self._connected = True
    
    def _disconnect(self):
        if self._connected:
            self.session.stop()
            self._connected = False

    def BDH(self, securities, fields, startDate, endDate, **kwargs):
        """ Equivalent to the Excel BDH Function.
        
            If securities are provided as a list, the returned DataFrame will
            have a MultiIndex.
        """
        params = {'startDate'       : startDate,
            'endDate'                 : endDate,
            'periodicityAdjustment'   : 'ACTUAL',
            'periodicitySelection'    : 'DAILY'}   
        params.update(kwargs)

        response = self._sendRequest('HistoricalData', securities, fields, params)
        
        data = []
        keys = []
        
        for msg in response:
            securityData = msg.getElement('securityData')
            fieldData = securityData.getElement('fieldData')
            fieldDataList = [fieldData.getValueAsElement(i) for i in range(fieldData.numValues())]
            
            df = pd.DataFrame()
            
            for field in fieldDataList:
                for v in [field.getElement(i) for i in range(field.numElements()) if field.getElement(i).name() != 'date']:
                    df.ix[field.getElementAsDatetime('date'), str(v.name())] = v.getValue()

            df.index = df.index.to_datetime()
            df.replace('#N/A History', np.nan, inplace=True)
            
            keys.append(securityData.getElementAsString('security'))

            if not df.empty:
                data.append(df)

        data = pd.concat(data, keys=keys, axis=1)
        return data
        
    def BDP(self, securities, fields, **kwargs):
        """ Equivalent to the Excel BDP Function.
        
            If either securities or fields are provided as lists, a DataFrame
            will be returned.
        """
        response = self._sendRequest('ReferenceData', securities, fields, kwargs)
        
        data = pd.DataFrame()
        
        for msg in response:
            securityData = msg.getElement('securityData')
            securityDataList = [securityData.getValueAsElement(i) for i in range(securityData.numValues())]
            
            for sec in securityDataList:
                fieldData = sec.getElement('fieldData')
                fieldDataList = [fieldData.getElement(i) for i in range(fieldData.numElements())]
                
                for fld in fieldDataList:
                    data.ix[sec.getElementAsString('security'), str(fld.name())] = fld.getValue()
        return data
        
    def BDS(self, securities, fields, **kwargs):
        """ Equivalent to the Excel BDS Function.
        
            If securities are provided as a list, the returned DataFrame will
            have a MultiIndex.
            
            You may pass a list of fields to a bulkRequest.  An appropriate
            Index will be generated, however such a DataFrame is unlikely to
            be useful unless the bulk data fields contain overlapping columns.
        """
        response = self._sendRequest('ReferenceData', securities, fields, kwargs)

        data = []
        keys = []
        
        for msg in response:
            securityData = msg.getElement('securityData')
            securityDataList = [securityData.getValueAsElement(i) for i in range(securityData.numValues())]
            
            for sec in securityDataList:
                fieldData = sec.getElement('fieldData')
                fieldDataList = [fieldData.getElement(i) for i in range(fieldData.numElements())]
                
                df = pd.DataFrame()
                
                for fld in fieldDataList:
                    for v in [fld.getValueAsElement(i) for i in range(fld.numValues())]:
                        s = pd.Series()
                        for d in [v.getElement(i) for i in range(v.numElements())]:
                            s[str(d.name())] = d.getValue()
                        df = df.append(s, ignore_index=True)

                if not df.empty:
                    keys.append(sec.getElementAsString('security'))
                    data.append(df)

        data = pd.concat(data, keys=keys, axis=0)
        data.index = data.index.get_level_values(0)
            
        return data
        
    def _sendRequest (self, requestType, securities, fields, elements):
        """ Prepares and sends a request then blocks until it can return 
            the complete response.
            
            Depending on the complexity of your request, incomplete and/or
            unrelated messages may be returned as part of the response.
        """
        request = self.refDataService.createRequest(requestType + 'Request')
        
        if isinstance(securities, str):
            securities = [securities]
        if isinstance(fields, str):
            fields = [fields]
        
        [ request.append('securities', security) for security in securities ]
        [ request.append('fields', field) for field in fields ]
        
        if requestType=='ReferenceData':
            for k, v in elements.items():
                override = request.getElement('overrides').appendElement()
                override.setElement('fieldId', k)
                override.setElement('value', v)
        else:
            for k, v in elements.items():
                if type(v) == datetime:
                    v = v.strftime('%Y%m%d')
                request.set(k, v)      
                
        self.session.sendRequest(request)

        response = []
        while True:
            event = self.session.nextEvent()
            for msg in event:
                if msg.hasElement('responseError'):
                    raise BLPRequestError('{0}'.format(msg.getElement('responseError')))
                if msg.hasElement('securityData'):
                    print(msg)
                    if requestType=='ReferenceData':
                        securityData = msg.getElement('securityData')
                        for i in range(securityData.numValues()):
                            sec = securityData.getValueAsElement(i)
                            if sec.hasElement('fieldExceptions') and (sec.getElement('fieldExceptions').numValues() > 0):
                                raise BLPRequestError('{0}'.format(sec.getElement('fieldExceptions')))
                            if sec.hasElement('securityError') and (sec.getElement('securityError').numValues() > 0):
                                raise BLPRequestError('{0}'.format(sec.getElement('securityError')))
                    if requestType=='HistoricalData':
                        if msg.getElement('securityData').hasElement('fieldExceptions') and (msg.getElement('securityData').getElement('fieldExceptions').numValues() > 0):
                            raise BLPRequestError('{0}'.format(msg.getElement('securityData').getElement('fieldExceptions')))
                        if msg.getElement('securityData').hasElement('securityError'):
                            raise BLPRequestError('{0}'.format(msg.getElement('securityData').getElement('securityError')))
                
                # no error occurs
                if msg.messageType() == requestType + 'Response':
                    response.append(msg)
                
            if event.eventType() == blpapi.Event.RESPONSE:
                break
                
        return response

    def __enter__ (self):
        self._connect()
        return self
        
    def __exit__ (self, exc_type, exc_val, exc_tb):
        self._disconnect()

    def __del__ (self):
        self._disconnect()

def main():
    """ Basic usage examples.
    
        Note that if any tickers have changed since these examples were written
        a RequestError will be raised.
    """
    try:
        blp = BLPService()
        
        # ==============================
        # = HistoricalRequest Examples =
        #===============================      
        # Requesting multiple fields returns a DataFrame with multiple columns.  Dates may also be passed as a datetime.
        print (blp.BDH('BMO CN Equity', 'PX_LAST', '20141231', '20150131'))
        print (blp.BDH('BNS CN Equity', ['PX_LAST', 'PX_VOLUME'], datetime(2014, 12, 31), datetime(2015, 1, 31)))
                
        # Requesting multiple securities returns a DataFrame with a MultiIndex.
        print (blp.BDH(['CM CN Equity', 'NA CN Equity'], ['PX_LAST', 'PX_VOLUME'], '20141231', '20150131'))

        # You may force any DataFrame to include a MultiIndex by passing the arguments as lists.
        print (blp.BDH(['NA CN Equity'], ['PX_LAST'], '20141231', '20150131'))
    
        # Keyword arguments are added to the request, allowing you to perform advanced queries.
        print (blp.BDH('TD CN Equity', 'PCT_CHG_INSIDER_HOLDINGS', '20141231', '20150131', periodicitySelection='WEEKLY'))
        
        blp._disconnect()
        
        # The BLPService Class can also be used as a ContextManager.
        with BLPService() as blp:
            # =============================
            # = ReferenceRequest Examples =
            # =============================
           
            # Requesting a single security/field or multiple securities or fields will return a DataFrame.
            print (blp.BDP('BBD/B CN Equity', 'GICS_SECTOR'))
            print (blp.BDP(['CNR CN Equity', 'CP CN Equity'], ['SECURITY_NAME_REALTIME', 'LAST_PRICE']))
            
            # You may force any request to return a DataFrame by passing the arguments as lists.
            print (blp.BDP(['MDA CN Equity'], ['NAME_RT']))
            
            # ========================
            # = BulkRequest Examples =
            # ========================
            # Requesting a single security and field will return a DataFrame.
            print (blp.BDS('CIG CN Equity','EQY_DVD_ADJUST_FACT'))
            
            # You may request multiple securities and/or fields.
            # This feature is generally not useful as the resulting DataFrame is ugly.
            print (blp.BDS(['CP CN Equity','CNR CN Equity'],'PG_REVENUE'))
            print (blp.BDS('CIG CN Equity',['EQY_DVD_ADJUST_FACT','DVD_HIST_ALL']))

    except BLPRequestError as e:
        print (e.value)
        raise
        
        
if __name__ == "__main__":
    try:
        pass
        #main()
    except KeyboardInterrupt:
        print ("Ctrl+C pressed. Stopping...")    
