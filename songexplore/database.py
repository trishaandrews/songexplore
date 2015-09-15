from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref

from songexplore.settings import params

url = "postgresql://%s:%s@%s/%s" %params

engine = create_engine(url)
Base = declarative_base()
Base.metadata.reflect(engine)

class Recs(Base):
    __table__ = Base.metadata.tables['recs']

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

