from rest_framework import serializers

from account.serializers import UserProfileSerializer
from item.models import Item, Comment, Photo, Rating


class ItemSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer()

    class Meta:
        model = Item


class CommentSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer()

    class Meta:
        model = Comment


class PhotoSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer()

    class Meta:
        model = Photo


class RatingSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer()

    class Meta:
        model = Rating


class CreateItemSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class UpdateItemSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()


class AddRatingSerializer(serializers.Serializer):
    rating = serializers.FloatField()


class AddCommentSerializer(serializers.Serializer):
    description = serializers.CharField()


class AddPhotoSerializer(serializers.Serializer):
    picture = serializers.ImageField()


class BoundingBoxSerializer(serializers.Serializer):
    min_latitude = serializers.FloatField()
    max_latitude = serializers.FloatField()
    min_longitude = serializers.FloatField()
    max_longitude = serializers.FloatField()

    def validate_values(self):
        return self.min_latitude <= self.max_latitude and self.min_longitude <= self.max_longitude

