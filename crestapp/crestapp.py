import ydb
from time import sleep
import requests
import json
import logging
import time
import urllib.parse

class CRestApp:
    """Class for working with Bitrix24 REST API"""
    def __init__(self, member_id = '', client_id = '', client_secret = '', ydb_session = False):
        self.__member_id = member_id
        self.user_agent = "CRestApp"
        self.inbound_hook = False
        self.oauth_url = 'https://oauth.bitrix.info/oauth/token/'
        self.app_id = client_id
        self.app_secret = client_secret
        
        self.__session = ydb_session

        settings = self.__getAppSettings()

        if settings == False:
            logging.warning("Need Install App")
            print({'status': False, 'error': 'Need Install App'})

    def installApp(self, arParams):
        result = {
            'rest_only': True,
            'install': False
        }

        if arParams.get('event') == 'ONAPPINSTALL' and arParams.get('auth'):
            result['install'] = self.__setAppSettings(arParams.get('auth'))
        elif arParams.get('PLACEMENT') == 'DEFAULT':
            result['rest_only'] = False
            arSettings = {
                'access_token': arParams.get('AUTH_ID'),
                'expires_in': arParams.get('AUTH_EXPIRES'),
                'application_token': arParams.get('APP_SID'),
                'refresh_token': arParams.get('REFRESH_ID'),
                'domain': arParams.get('DOMAIN'),
                'client_endpoint': 'https://' + arParams.get('DOMAIN') + '/rest/',
            }
            result['install'] = self.__setAppSettings(arSettings)

        return self.__getAppSettings()


    def refresh_tokens(self):
        """Refresh access token from Bitrix OAuth server
        :return: dict with refreshing status
        """

        # Make call to oauth server
        result = requests.get(self.oauth_url, timeout=10, params={
            'grant_type': 'refresh_token',
            'client_id': self.app_id,
            'client_secret': self.app_secret,
            'refresh_token': self.refresh_token
        }).text

        try:
            result_json = json.loads(result)
            logging.debug("access_token: {access_token}".format(access_token=result_json['access_token']))

            # Renew tokens
            self.access_token = result_json['access_token']
            self.refresh_token = result_json['refresh_token']

            arSettings = {
                'member_id'       : self.__member_id,
                'client_endpoint' : self.endpoint,
                'access_token'    : self.access_token,
                'refresh_token'   : self.refresh_token
            }
            self.__setAppSettings(arSettings)
            return {'status': True}

        except (ValueError, KeyError):
            logging.warning("Need Install App")
            return {'status': False, 'error': 'Error on decode OAuth response', 'response': result}

    def __setAppSettings(self, arSettings):
        if self.__member_id and  arSettings.get("client_endpoint") and arSettings.get("access_token") and arSettings.get("refresh_token"):
          query = """
          DECLARE $member_id AS Utf8;
          DECLARE $client_endpoint AS Utf8;
          DECLARE $access_token AS Utf8;
          DECLARE $refresh_token AS Utf8;
          DECLARE $timestamp AS Timestamp;
          UPSERT INTO `portals`  ( `member_id`, `client_endpoint`, `access_token`, `refresh_token`, `timestamp` ) VALUES ( $member_id, $client_endpoint, $access_token, $refresh_token, $timestamp );
          """

          prepared_values = {
            '$member_id': self.__member_id,
            '$timestamp': int(time.time()*1000000), 
            '$client_endpoint': arSettings.get('client_endpoint'),
            '$access_token': arSettings.get('access_token'),
            '$refresh_token': arSettings.get('refresh_token')
          }

          prepared_query = self.__session.prepare(query)

          self.__session.transaction(ydb.SerializableReadWrite()).execute( prepared_query, prepared_values, commit_tx=True )
          return True
        else:
          return False

    # return mixed setting application for query
    def __getAppSettings(self):
        try:
          query = 'DECLARE $member_id AS Utf8; SELECT * FROM `portals`  WHERE `member_id` = $member_id;'
          prepared_query = self.__session.prepare(query)
          res = self.__session.transaction(ydb.SerializableReadWrite()).execute( prepared_query, { '$member_id': self.__member_id }, commit_tx=True )
          settings = res[0].rows[0]

          self.endpoint = settings.get("client_endpoint")
          self.access_token = settings.get("access_token")
          self.refresh_token = settings.get("refresh_token")
          return True
        except:
          return False

    def call(self, method: str, params: dict = {}, data: dict = {}, refresh = False) -> dict:
        """ Makes call to bitrix24 REST and return result
        :param method: REST API Method you want to call
        :params: Request params
        :return: Call result
        """

        result = {}
        if self.inbound_hook:
            uri = self.inbound_hook + '/' + method
        else:
            uri = self.endpoint + method
            if len(data):
                data['auth'] = self.access_token
                params = False
            else:
                data = False
                params['auth'] = self.access_token

        r = ""
        try:
            logging.info("Request: {uri}, {params}".format(uri=uri,params=params))
            r = requests.post(
                uri,
                json=params,
                data=data,
                timeout=10,
                headers={
                    'User-Agent': self.user_agent
                }
            ).text
            logging.info("Response: {str}".format(str=r))
            result = json.loads(r)
        except requests.exceptions.ReadTimeout:
            return {'status': False, 'error': 'Timeout waiting expired'}
        except requests.exceptions.ConnectionError:
            if 'https://' in self.endpoint:
                self.endpoint = self.endpoint.replace('https://', 'http://')
                return self.call(method, params)
            else:
                return {'status': False, 'error': 'Could not connect to bx24 resource', 'uri': uri}

        if refresh == False and (result.get('error') == 'NO_AUTH_FOUND' or result.get('error') == 'expired_token' or result.get('error') == 'invalid_token'):
            result = self.refresh_tokens()
            if result['status'] is not True:
                return result

            # Repeat API request after renew token
            result = self.call(method, params, refresh = True)

        if result.get('error'):
            logging.error("ERROR: {str}".format(str=result.get('error')))
        return result

    def __http_build_query(self, data):
        parents = list()
        pairs = dict()

        def renderKey(parents):
            depth, outStr = 0, ''
            for x in parents:
                s = "[%s]" if depth > 0 or isinstance(x, int) else "%s"
                outStr += s % str(x)
                depth += 1
            return outStr

        def r_urlencode(data):
            if isinstance(data, list) or isinstance(data, tuple):
                for i in range(len(data)):
                    parents.append(i)
                    r_urlencode(data[i])
                    parents.pop()
            elif isinstance(data, dict):
                for key, value in data.items():
                    parents.append(key)
                    r_urlencode(value)
                    parents.pop()
            else:
                pairs[renderKey(parents)] = str(data)

            return pairs
        return urllib.parse.urlencode(r_urlencode(data))
    
    def callBatch(self, batch: dict, batch_params: dict = {}, halt=False) -> dict:
        """ Creates Bitrix Batch and calls them
        :param batch: Dict  with call name and method to call in batch. Eg. {"deals": "crm.deal.list", "fields": "crm.deal.fields"}
        :param halt: Stop batch if error in method
        :batch params: Params for batch methods. Eg. {"deals": ['select[]=TITLE', 'order[ID]=DSC', 'filter[<ID]=92']}
        :return: Batch result
        """
        request = {'halt': halt}
        if self.inbound_hook:
            uri = self.inbound_hook + '/' + 'batch'
        else:
            uri = self.endpoint + 'batch'
            request['auth'] = self.access_token

        for key, params in batch_params.items():
            batch[key] += "?{}".format(self.__http_build_query(params))
        logging.info("Batch: {batch}".format(batch=batch))
        request['cmd'] = batch

        result = self.call('batch', request)
        return result
