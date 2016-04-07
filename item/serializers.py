from rest_framework import serializers

from account.serializers import UserProfileSerializer
from item.models import Item


class ItemSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer()

    class Meta:
        model = Item


class CreateItemSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
