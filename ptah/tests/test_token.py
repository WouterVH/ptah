import transaction
from memphis import config
from datetime import timedelta

from base import Base


class TestTokenType(Base):

    def tearDown(self):
        config.cleanUp(self.__class__.__module__)
        super(TestTokenType, self).tearDown()

    def test_token(self):
        from ptah import token

        tt = token.TokenType('unique-id', timedelta(minutes=20))
        self._init_memphis()

        t = token.service.generate(tt, 'data')
        transaction.commit()

        self.assertEqual(token.service.get(t), 'data')
        self.assertEqual(token.service.getByData(tt, 'data'), t)

        token.service.remove(t)
        self.assertEqual(token.service.get(t), None)

    def test_token_type(self):
        from ptah import token

        tt1 = token.TokenType('unique-id', timedelta(minutes=20))
        tt2 = token.TokenType('unique-id', timedelta(minutes=20))

        self.assertRaises(config.ConflictError, self._init_memphis)

    def test_token_remove_expired(self):
        pass