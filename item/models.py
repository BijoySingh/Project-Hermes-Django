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
                (cls.UPVOTE, 'Upvote'),
                (cls.DOWNVOTE, 'Downvote'),
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
    BASE_SCORE = 10.0

    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    flags = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    experience = models.FloatField(default=0)

    @staticmethod
    def convert_to_score(count, scale, values=(1, 10, 50, 200, 1000), scores=(1, 2, 4, 8, 16)):
        for index in reversed(range(len(values))):
            if values[index] < count:
                return scores[index]

        return 0.0

    def recalculate_score(self):
        return self.BASE_SCORE - self.convert_to_score(self.flags, 50, values=(0, 4, 8, 16, 32)) \
               - self.convert_to_score(self.downvotes, 20, values=(0, 5, 10, 20, 50)) \
               + self.convert_to_score(self.upvotes, 10)


class Reaction(models.Model):
    reaction = models.IntegerField(choices=ReactionChoices.get(), default=ReactionChoices.NONE)
    reactable = models.ForeignKey(Reactable, related_name='reactions')
    author = models.ForeignKey(UserProfile)
    timestamp = models.DateTimeField(auto_now_add=True)


class Comment(Reactable):
    item = models.ForeignKey(Item, related_name='comments')
    author = models.ForeignKey(UserProfile)
    description = models.TextField()

    class Meta:
        unique_together = [['item', 'author']]

    def recalculate_score(self):
        score = super(self).recalculate_score()
        self.author.reputation += (score - self.experience)
        self.experience = score


class Photo(Reactable):
    item = models.ForeignKey(Item, related_name='photos')
    author = models.ForeignKey(UserProfile)
    picture = models.ImageField()

    def recalculate_score(self):
        score = super(self).recalculate_score()
        self.author.reputation += (score - self.experience)
        self.experience = score