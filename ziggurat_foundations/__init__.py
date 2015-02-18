__version__ = {'major': 0, 'minor': 4, 'patch': 3}


def make_passwordmanager():
    from cryptacular.bcrypt import BCRYPTPasswordManager
    from cryptacular.core import DelegatingPasswordManager
    from ziggurat_foundations.utils import PlaceholderPasswordChecker
    return DelegatingPasswordManager(
        preferred=BCRYPTPasswordManager(),
        fallbacks=(PlaceholderPasswordChecker(),)
    )

# this maps models together during runtime so we can access them in methods:
#
# def foo(self):
#     query(self, self.OtherModel)
#


def ziggurat_model_init(*k, **kw):

    for cls in k:
        if cls.__name__ == 'User':
            if kw.get('passwordmanager'):
                cls.passwordmanager = kw['passwordmanager']
            else:
                cls.passwordmanager = make_passwordmanager()
        for cls2 in k:
            setattr(cls, cls2.__name__, cls2)
