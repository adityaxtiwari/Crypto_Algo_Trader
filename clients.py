from deribit_api import RestClient

class Clients:
    def __init__(self):
        pass


    def authenticate(self):
        # testing version
        url = "wss://test.deribit.com/ws/api/v2"
        # real
        # url = "wss://www.deribit.com/ws/api/v2"
        deribitClient = RestClient(key="zMFpvM4s", secret="1BZkMN4zYheUX2LZ_VG5AjAsYHdvBkc9a6zvzTCDO24",url=url)

        return {"deribit": deribitClient, "url":url}


