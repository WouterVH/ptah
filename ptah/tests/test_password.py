import unittest
import ptah
from ptah import form, config

from base import Base


class Principal(object):

    def __init__(self, uri, name, login):
        self.uri = uri
        self.name = name
        self.login = login


class TestPasswordSchema(Base):

    def test_password_required(self):
        self._init_ptah()
        from ptah.password import PasswordSchema

        pwdSchema = PasswordSchema.bind(params={})

        data, errors = pwdSchema.extract()
        self.assertEqual(len(errors), 2)
        self.assertEqual(errors[0].field.name, 'password')

    def test_password_equal(self):
        self._init_ptah()
        from ptah.password import PasswordSchema

        pwdSchema = PasswordSchema.bind(
            params={'password': '12345', 'confirm_password': '123456'})
        data, errors = pwdSchema.extract()

        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0].field, form.Fieldset)
        self.assertEqual(
            errors[0].msg[0],
            "Password and Confirm Password should be the same.")

    def test_password(self):
        self._init_ptah()
        from ptah.password import PasswordSchema

        pwdSchema = PasswordSchema.bind(
            params={'password': '12345', 'confirm_password': '12345'})
        data, errors = pwdSchema.extract()
        self.assertEqual(len(errors), 0)

    def test_password_validator(self):
        from ptah.password import passwordValidator, PasswordTool

        vp = PasswordTool.validate

        def validatePassword(self, pwd):
            return 'Error'

        PasswordTool.validate = validatePassword

        self.assertRaises(
            form.Invalid, passwordValidator, None, 'pwd')

        PasswordTool.validate = vp


class TestSHAPasswordManager(unittest.TestCase):

    def test_password_ssha(self):
        from ptah.password import SSHAPasswordManager

        manager = SSHAPasswordManager()

        password = u"right \N{CYRILLIC CAPITAL LETTER A}"
        encoded = manager.encode(password, salt="")

        self.assertEqual(encoded, '{ssha}BLTuxxVMXzouxtKVb7gLgNxzdAI=')
        self.assertTrue(manager.check(encoded, password))
        self.assertFalse(manager.check(encoded, password + u"wrong"))

        encoded = manager.encode(password)
        self.assertTrue(manager.check(encoded, password))


class TestPlainPasswordManager(unittest.TestCase):

    def test_password_plain(self):
        from ptah.password import PlainPasswordManager

        manager = PlainPasswordManager()

        password = u"test pwd"
        encoded = manager.encode(password, salt="")

        self.assertEqual(encoded, '{plain}test pwd')
        self.assertTrue(manager.check(encoded, password))
        self.assertTrue(manager.check(password, password))
        self.assertFalse(manager.check(encoded, password + u"wrong"))

        encoded = manager.encode(password)
        self.assertTrue(manager.check(encoded, password))


class TestPasswordSettings(Base):

    def test_password_settings(self):
        self._init_ptah()

        from ptah.password import \
             PlainPasswordManager, SSHAPasswordManager

        ptah.PWD_CONFIG['manager'] = 'unknown'

        self.assertIsInstance(ptah.pwd_tool.manager, PlainPasswordManager)

        ptah.PWD_CONFIG['manager'] = 'ssha'

        self.assertIsInstance(ptah.pwd_tool.manager, SSHAPasswordManager)


class TestPasswordChangerDecl(Base):

    def tearDown(self):
        config.cleanup_system(self.__class__.__module__)
        super(TestPasswordChangerDecl, self).tearDown()

    def test_password_changer_decl(self):
        import ptah

        @ptah.password_changer('test-schema')
        def changer(schema):
            """ """

        self._init_ptah()

        from ptah.password import PASSWORD_CHANGER_ID
        changers = config.get_cfg_storage(PASSWORD_CHANGER_ID)

        self.assertIn('test-schema', changers)
        self.assertIs(changers['test-schema'], changer)

    def test_password_changer_decl_conflict(self):
        import ptah

        @ptah.password_changer('test-schema')
        def changer(schema):
            """ """

        @ptah.password_changer('test-schema')
        def changer2(schema):
            """ """

        self.assertRaises(config.ConflictError, self._init_ptah)

    def test_password_changer(self):
        import ptah

        @ptah.password_changer('test-schema')
        def changer(schema):
            """ """

        self._init_ptah()

        p = Principal('test-schema:numbers_numbers', 'name', 'login')
        self.assertTrue(ptah.pwd_tool.can_change_password(p))

        p = Principal('unknown-schema:numbers_numbers', 'name', 'login')
        self.assertFalse(ptah.pwd_tool.can_change_password(p))


class TestPasswordTool(Base):

    def tearDown(self):
        config.cleanup_system(self.__class__.__module__)
        super(TestPasswordTool, self).tearDown()

    def test_password_encode(self):
        ptah.PWD_CONFIG['manager'] = 'plain'

        encoded = ptah.pwd_tool.encode('12345')
        self.assertEqual(encoded, '{plain}12345')

    def test_password_check(self):
        ptah.PWD_CONFIG['manager'] = 'ssha'

        self.assertFalse(ptah.pwd_tool.check('12345', '12345'))
        self.assertTrue(ptah.pwd_tool.check('{plain}12345', '12345'))
        self.assertFalse(ptah.pwd_tool.check('{plain}12345', '123455'))
        self.assertFalse(ptah.pwd_tool.check('{unknown}12345', '123455'))

    def test_password_passcode(self):
        p = Principal('test-schema:test', 'name', 'login')
        principals = {'test-schema:test': p}

        @ptah.resolver('test-schema')
        def resolver(uri):
            return principals.get(uri)

        self._init_ptah()

        token = ptah.pwd_tool.generate_passcode(p)
        self.assertIsNotNone(token)

        newp = ptah.pwd_tool.get_principal(token)
        self.assertIs(newp, p)

        ptah.pwd_tool.remove_passcode(token)

        newp = ptah.pwd_tool.get_principal(token)
        self.assertIsNone(newp)

    def test_password_change_password(self):
        p = Principal('test-schema:test', 'name', 'login')
        principals = {'test-schema:test': p}

        @ptah.resolver('test-schema')
        def resolver(uri):
            return principals.get(uri)

        @ptah.password_changer('test-schema')
        def changer(principal, password):
            p.password = password

        self._init_ptah()

        token = ptah.pwd_tool.generate_passcode(p)
        self.assertIsNotNone(token)

        newp = ptah.pwd_tool.get_principal(token)
        self.assertIs(newp, p)

        self.assertTrue(ptah.pwd_tool.change_password(token, '12345'))
        self.assertEqual(p.password, '{plain}12345')

        newp = ptah.pwd_tool.get_principal(token)
        self.assertIsNone(newp)

        self.assertFalse(ptah.pwd_tool.change_password('unknown', '12345'))

    def test_password_validate(self):
        ptah.PWD_CONFIG['min_length'] = 5
        self.assertEqual(ptah.pwd_tool.validate('1234'),
                         'Password should be at least 5 characters.')

        ptah.PWD_CONFIG['letters_digits'] = True
        self.assertEqual(ptah.pwd_tool.validate('123456'),
                         'Password should contain both letters and digits.')

        ptah.PWD_CONFIG['letters_mixed_case'] = True
        self.assertEqual(ptah.pwd_tool.validate('abs456'),
                         'Password should contain letters in mixed case.')

        self.assertIsNone(ptah.pwd_tool.validate('aBs456'))
