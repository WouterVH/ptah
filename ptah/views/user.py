""" add/edit user """
from zope import interface
from zope.component import getUtility

from webob.exc import HTTPFound
from memphis import config, view, form

from ptah.models import User, Session
from ptah.interfaces import _, IPtahUser, IPasswordTool
from ptah.interfaces import IManageAction, IManageUserAction

from schemas import CreateUserSchema, ManagerChangePasswordSchema


class CreateUserAction(object):
    config.utility(name='create-user')
    interface.implements(IManageAction)

    title = _('Create user')
    action = 'create-user.html'

    def available(self):
        return True


class CreateUserForm(form.Form):
    view.pyramidView('create-user.html', route='ptah-manage')

    label = _('Create new user')
    fields = form.Fields(CreateUserSchema)

    @form.button(_('Create'), primary=True)
    def create(self):
        data, errors = self.extractData()

        if errors:
            self.message(errors, 'form-error')
            return

        # create user
        user = User(data['fullname'], data['login'], data['login'])
        
        if not data['validate']:
            user.validated = True

        if data['suspend']:
            user.suspended = True

        # set password
        passwordtool = getUtility(IPasswordTool)
        user.password = passwordtool.encodePassword(data['password'])
        Session.add(user)
        Session.flush()

        self.message('User has been created.', 'success')
        raise HTTPFound(location='./')

        #event.notify(ObjectCreatedEvent(item))


class Info(object):
    config.utility(name='user-info')
    interface.implements(IManageUserAction)

    title = _('Information')
    action = 'index.html'

    def available(self, principal):
        return True


class UserInfo(view.View):
    view.pyramidView('index.html', IPtahUser,
                     route = 'ptah-manage', default = True,
                     template = view.template('ptah.views:user.pt'))

    def update(self):
        request = self.request

        user = self.context.user

        if 'activate' in request.POST:
            user.suspended = False
            self.message("Account has been activated.", 'info')

        if 'suspend' in request.POST:
            user.suspended = True
            self.message("Account has been suspended.", 'info')
            
        if 'validate' in request.POST:
            user.validated = True
            self.message("Account  has been validated.", 'info')


class ChangePasswordAction(object):
    config.utility(name='user-password')
    interface.implements(IManageUserAction)

    title = _('Change password')
    action = 'change-password.html'

    def available(self, principal):
        return True


class ChangePassword(form.Form):
    view.pyramidView('change-password.html', IPtahUser, route = 'ptah-manage')

    fields = form.Fields(ManagerChangePasswordSchema)

    label = _('Change password')
    description = _('Please specify password for this users.')
    
    @form.button(_('Change'), primary=True)
    def change(self):
        data, errors = self.extractData()

        if errors:
            self.message(errors, 'form-error')
            return

        self.context.user.password = \
            getUtility(IPasswordTool).encodePassword(data['password'])

        self.message("User password has been changed.")
