from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST

from item.models import Item
from item.serializers import CreateItemSerializer, ItemSerializer


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def create(self, request, *args, **kwargs):
        serialized_data = CreateItemSerializer(data=request.data)
        if serialized_data.is_valid():
            item = Item.objects.filter(user=request.user, location=serialized_data.validated_data['location']).first()
            if not item:
                item = Item.objects.create(
                        latitude=serialized_data.validated_data['latitude'],
                        longitude=serialized_data.validated_data['longitude'],
                        title=serialized_data.validated_data['title'],
                        description=serialized_data.validated_data['description'],
                        user=request.user,
                )
            return Response(self.serializer_class(item).data)
        else:
            return Response(serialized_data.errors, status=HTTP_400_BAD_REQUEST)

