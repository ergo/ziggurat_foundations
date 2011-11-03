from sqlalchemy import *
import sqlalchemy as sa
from sqlalchemy.orm import *
from sqlalchemy.ext.declarative import declarative_base, declared_attr

Base= declarative_base()


class BaseModel(object):
    """ base class for  all other models to inherit """
    pass
            
                

class ResourceMixin(BaseModel):    
    
    __possible_permissions__ = ()
    
    @declared_attr
    def __tablename__(cls):
        return 'resources'
    
    @declared_attr
    def resource_id(cls):
        return sa.Column(sa.BigInteger(), primary_key=True, nullable=False)
    
    @declared_attr
    def resource_name(cls):
        return sa.Column(sa.Unicode(100), nullable=False)
    
    @declared_attr
    def resource_type(cls):
        return sa.Column(sa.Unicode(30), nullable=False)


    
    __mapper_args__ = {'polymorphic_on': resource_type
                       }
    __table_args__ = {
                      'mysql_engine':'InnoDB',
                      'mysql_charset':'utf8'
                      }

class Resource(ResourceMixin, Base):
    pass

configure_mappers()

print Resource.__mapper__.polymorphic_on