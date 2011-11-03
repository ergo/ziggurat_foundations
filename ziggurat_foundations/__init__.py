__version__ = {'major':0, 'minor':1}


# this maps models together during runtime so we can access them in methods:
#
# def foo(self):
#     query(self, self.OtherModel)
#

def ziggurat_model_init(*k, **kw):
    for cls in k:
        for cls2 in k:
            setattr(cls, cls2.__name__, cls2)
                
