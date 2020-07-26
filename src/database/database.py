
from sqlalchemy import Column, String, Integer, ForeignKey,create_engine, Boolean, Text, select, event, func
from sqlalchemy.orm import relationship, sessionmaker, column_property
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
import static

class Database:
    def __init__(self):
        self.engine = create_engine(f"sqlite:///{static.DATABASE_NAME}")
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        Base.metadata.create_all(self.engine)
        self.commit()

    def commit(self):
        self.session.commit()

    def close(self):
        self.engine.dispose()



class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer(), ForeignKey('users.id'))
    post_id = Column(String(10), primary_key=True)
    author = Column(String(100))
    receiver = Column(String(100))
    message = Column(Text(10000),default=None)
    feedback_type = Column(Integer())
    count_to_total = Column(Boolean(),default=True)

    def __init__(self, post_id, author, receiver, feedback_type, message=None, count_to_total=True):
        self.post_id = post_id
        self.author = author
        self.receiver = receiver
        self.message = message
        self.feedback_type = feedback_type
        self.count_to_total = count_to_total

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer(), primary_key=True)
    name = Column(String(100), unique=True)
    positive = column_property(select([func.count(Feedback.feedback_type)]).where(Feedback.receiver==name and Feedback.feedback_type==1))
    neutral = column_property(select([func.count(Feedback.feedback_type)]).where(Feedback.receiver==name and Feedback.feedback_type==0))
    negative = column_property(select([func.count(Feedback.feedback_type)]).where(Feedback.receiver==name and Feedback.feedback_type==-1))
    total = column_property(select([func.sum(Feedback.feedback_type)]).where(Feedback.receiver==name and (Feedback.feedback_type==1 or Feedback.feedback_type==-1)))
    feedback = relationship("Feedback")

    def __init__(self, name):
        self.name = name

    def get_total(self):
        if not self.total:
            return 0
        return self.total


