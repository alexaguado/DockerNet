__author__ = 'alejandroaguado'

import web

httpmsgtypes={"Success":"200","NotFound":"404","Conflict":"409","BadRequest":"400","InternalServer":"500", "auth":"401"}

class httpResponse(web.HTTPError):
    def __init__(self, type, message, info='', auth=None):
        status = type+' '+message
        headers = {'Content-Type': 'application/json', 'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'Origin, X-Requested-With, Content-Type, Accept, Authorization'}
        if auth:
            headers[auth[0]]=auth[1]
        data = info
        web.HTTPError.__init__(self, status, headers, data)

'''
class NotFoundError(web.HTTPError):
    def __init__(self,message,info=''):
        status = '404 '+message
        headers = {'Content-Type': 'text/html'}
        data = info
        web.HTTPError.__init__(self, status, headers, data)

class InternalServerError(web.HTTPError):
    def __init__(self,message,info=''):
        status = '500 '+message
        headers = {'Content-Type': 'text/html'}
        data = info
        web.HTTPError.__init__(self, status, headers, data)

class BadRequestError(web.HTTPError):
    def __init__(self,message,info=''):
        status = '400 '+message
        headers = {'Content-Type': 'text/html'}
        data = info
        web.HTTPError.__init__(self, status, headers, data)

class Successful(web.HTTPError):
    def __init__(self,message,info=''):
        status = '200 '+message
        headers = {'Content-Type': 'application/json'}
        data = info
        web.HTTPError.__init__(self, status, headers, data)

class Conflict(web.HTTPError):
    def __init__(self,message,info=''):
        status = '409 '+message
        headers = {'Content-Type': 'application/json'}
        data = info
        web.HTTPError.__init__(self, status, headers, data)
'''
