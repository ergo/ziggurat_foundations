def reactor_model_init(*k, **kw):
    for cls in k:
        for cls2 in k:
            setattr(cls, cls2.__name__, cls2)
                
