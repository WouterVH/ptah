""" forbidden view """
import urllib
from webob.exc import HTTPFound, HTTPForbidden
from zope.component import getUtility

from memphis import view
from ptah.interfaces import IAuthentication


class Forbidden(view.View):
    view.pyramidView(context = HTTPForbidden, 
                     layout='ptah-exception',
                     template = view.template('ptah.views:forbidden.pt'))

    def update(self):
        self.__parent__ = view.DefaultRoot()

        auth = getUtility(IAuthentication)

        request = self.request
        user = auth.getCurrentLogin(request)
        if user is None:
            request.response.status = HTTPFound.code
            request.response.headers['location'] = '%s/login.html?%s'%(
                request.application_url, urllib.urlencode(
                    {'came_from': request.url}))
            return

        self.request.response.status = HTTPForbidden.code
