from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, DateTime, Float, Boolean
from dateutil.parser import parse

Base = declarative_base()


class Story(Base):
    __tablename__ = 'stories'

    id = Column(Integer, primary_key=True)
    stories_id = Column(Integer)
    project_id = Column(Integer)
    model_id = Column(Integer)
    model_score = Column(Float)
    published_date = Column(DateTime)
    queued_date = Column(DateTime)
    processed_date = Column(DateTime)
    posted_date = Column(DateTime)
    above_threshold = Column(Boolean)

    def __repr__(self):
        return '<Story id={}>'.format(self.id)

    @staticmethod
    def from_mc_story(story):
        s = Story()
        s.stories_id = story['stories_id']
        s.published_date = parse(story['publish_date'])
        return s