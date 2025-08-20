import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    user_id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.Integer, unique=True, nullable=False)
    first_name = sq.Column(sq.String(50))
    second_name = sq.Column(sq.String(50))
    user_age = sq.Column(sq.Integer)
    city = sq.Column(sq.String(50))
    user_sex = sq.Column(sq.Integer)
    last_updated_info = sq.Column(sq.DateTime)

class Candidate(Base):
    __tablename__ = 'candidates'

    candidate_id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.Integer, unique=True, nullable=False)
    first_name = sq.Column(sq.String(50))
    last_name = sq.Column(sq.String(50))
    profile_url = sq.Column(sq.String(255))
    
    photos = relationship("Photo", back_populates="candidate")

class Photo(Base):
    __tablename__ = 'photos'

    photo_id = sq.Column(sq.Integer, primary_key=True)
    candidate_id = sq.Column(sq.Integer, sq.ForeignKey('candidates.candidate_id'), nullable=False)
    owner_id = sq.Column(sq.Integer)
    count_likes = sq.Column(sq.Integer)
    attachment = sq.Column(sq.String(255))
    
    candidate = relationship("Candidate", back_populates="photos")

class UserInteraction(Base):
    __tablename__ = 'userinteractions'

    user_inter_id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey('users.user_id'), nullable=False)
    candidate_id = sq.Column(sq.Integer, sq.ForeignKey('candidates.candidate_id'), nullable=False)
    status = sq.Column(sq.String(20)) # 'seen', 'liked'
    created_at = sq.Column(sq.DateTime, server_default=sq.func.now())
    
    user = relationship(User)
    candidate = relationship(Candidate)
