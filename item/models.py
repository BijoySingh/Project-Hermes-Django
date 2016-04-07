from __future__ import unicode_literals

from django.db import models

from account.models import UserProfile


class ItemStatusChoices:
    """
    Class for the choices in the status field of an Item
    """

    VERIFIED = 0
    UNVERIFIED = 1
    DELETED = 2
    REMOVED = 3

    @classmethod
    def get(cls):
        return [(cls.VERIFIED, 'Verified'),
                (cls.UNVERIFIED, 'Unverified'),
                (cls.DELETED, 'Deleted'),
                (cls.REMOVED, 'Removed')]


class ReactionChoices:
    NONE = 0
    UPVOTE = 1
    DOWNVOTE = 2
    FLAG = 3

    @classmethod
    def get(cls):
        return [(cls.NONE, 'None'),
                (cls.UPVOTE, 'Like'),
                (cls.DOWNVOTE, 'Dislike'),
                (cls.FLAG, 'Flag')]


class Item(models.Model):
    """
    The Location Based Crowd sourced object
    """

    title = models.TextField(max_length=256, blank=False)
    description = models.TextField(blank=True)
    author = models.ForeignKey(UserProfile)
    rating = models.FloatField(default=0.0)
    latitude = models.FloatField()
    longitude = models.FloatField()
    flags = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(choices=ItemStatusChoices.get(), default=ItemStatusChoices.UNVERIFIED)


class Rating(models.Model):
    item = models.ForeignKey(Item, related_name='ratings')
    author = models.ForeignKey(UserProfile)
    rating = models.FloatField(default=0.0)

    class Meta:
        unique_together = [['item', 'author']]


class Reactable(models.Model):
    author = models.ForeignKey(UserProfile)
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    flags = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)


class Reaction(models.Model):
    reaction = models.IntegerField(choices=ReactionChoices.get(), default=ReactionChoices.NONE)
    reactable = models.ForeignKey(Reactable)
    author = models.ForeignKey(UserProfile)
    timestamp = models.DateTimeField(auto_now_add=True)


class Comment(Reactable):
    item = models.ForeignKey(Item, related_name='comments')
    description = models.TextField()

    class Meta:
        unique_together = [['item', 'author']]


class Photo(Reactable):
    item = models.ForeignKey(Item, related_name='photos')
    picture = models.ImageField()