from django.shortcuts import get_object_or_404

# Create your views here.
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN

from item.models import Item, Comment, Reaction, ReactionChoices, Photo
from item.serializers import CreateItemSerializer, ItemSerializer, BoundingBoxSerializer, CommentSerializer, \
    PhotoSerializer, UpdateItemSerializer


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
                        author=request.user,
                )
            return Response(self.serializer_class(item).data)
        else:
            return Response(serialized_data.errors, status=HTTP_400_BAD_REQUEST)

    @list_route(methods=['POST'], permission_classes=[])
    def search_bounding_box(self, request):
        serialized_data = BoundingBoxSerializer(data=request.data)

        if serialized_data.is_valid():
            min_latitude = serialized_data.validated_data['min_latitude']
            max_latitude = serialized_data.validated_data['max_latitude']
            min_longitude = serialized_data.validated_data['min_longitude']
            max_longitude = serialized_data.validated_data['max_longitude']

            items = self.get_queryset().filter(latitude__range=[min_latitude, max_latitude],
                                               longitude__range=[min_longitude, max_longitude])
            response = {
                'results': self.serializer_class(items, many=True).data
            }
            return Response(response)
        else:
            return Response({'success': False, 'message': 'Incorrect Data Sent'}, status=HTTP_400_BAD_REQUEST)

    @detail_route(permission_classes=[IsAuthenticated])
    def get_user_comment(self, request, pk):
        item = get_object_or_404(Item, pk=pk)
        comment = Comment.objects.filter(author__user=request.user, item=item).first()
        if comment:
            response = {
                'success': True,
                'result': CommentSerializer(comment).data
            }
            return Response(response)
        else:
            return Response({'success': False})

    @detail_route()
    def get_posts(self, request, pk):
        item = get_object_or_404(Item, pk=pk)
        comments = item.comments.all()
        response = {
            'results': CommentSerializer(comments, many=True).data
        }
        return Response(response)

    @detail_route()
    def get_photos(self, request, pk):
        item = get_object_or_404(Item, pk=pk)
        photos = item.photos.all()
        response = {
            'results': PhotoSerializer(photos, many=True).data
        }
        return Response(response)

    def update(self, request, *args, **kwargs):
        serialized_data = UpdateItemSerializer(data=request.data)
        item = self.get_object()
        if item.author.user != request.user:
            return Response({'success': False, 'message': 'Unauthorized Access'}, status=HTTP_403_FORBIDDEN)

        if serialized_data.is_valid():
            item.title = serialized_data.validated_data['title']
            item.description = serialized_data.validated_data['description']
            item.save()

            return Response(self.serializer_class(item).data)
        else:
            return Response({'success': False, 'message': 'Incorrect Data Sent'}, status=HTTP_400_BAD_REQUEST)


class ReactableViewSet(viewsets.ModelViewSet):
    @staticmethod
    def upvote(request, pk, reactable):
        reaction = Reaction.objects.filter(author__user=request.user).exclude(reaction=ReactionChoices.FLAG).first()
        if reaction:
            reaction.reaction = ReactionChoices.UPVOTE
            reaction.save()

            if reaction.reaction == ReactionChoices.DOWNVOTE:
                reactable.upvotes += 1
                reactable.upvotes -= 1
                reactable.save()

            if reaction.reaction == ReactionChoices.NONE:
                reactable.upvotes += 1
                reactable.save()

        else:
            Reaction.objects.create(
                reaction=ReactionChoices.UPVOTE,
                reactable=reactable,
                author=request.user
            )
            reactable.upvotes += 1
            reactable.save()

        return reactable

    @staticmethod
    def downvote(request, pk, reactable):
        reaction = Reaction.objects.filter(author__user=request.user).exclude(reaction=ReactionChoices.FLAG).first()
        if reaction:
            reaction.reaction = ReactionChoices.DOWNVOTE
            reaction.save()

            if reaction.reaction == ReactionChoices.UPVOTE:
                reactable.upvotes -= 1
                reactable.upvotes += 1
                reactable.save()

            if reaction.reaction == ReactionChoices.NONE:
                reactable.downvotes += 1
                reactable.save()

        else:
            Reaction.objects.create(
                reaction=ReactionChoices.DOWNVOTE,
                reactable=reactable,
                author=request.user
            )
            reactable.downvotes += 1
            reactable.save()

        return reactable


    @staticmethod
    def flag(request, pk, reactable):
        reaction = Reaction.objects.filter(author__user=request.user, reaction=ReactionChoices.FLAG).first()
        if not reaction:
            Reaction.objects.create(
                reaction=ReactionChoices.FLAG,
                reactable=reactable,
                author=request.user
            )
            reactable.flags += 1
            reactable.save()

        return reactable

    @staticmethod
    def unflag(request, pk, reactable):
        reaction = Reaction.objects.filter(author__user=request.user, reaction=ReactionChoices.FLAG).first()
        if reaction:
            reaction.delete()
            reactable.flags -= 1
            reactable.save()

        return reactable

    @staticmethod
    def unvote(request, pk, reactable):
        reaction = Reaction.objects.filter(author__user=request.user).exclude(reaction=ReactionChoices.FLAG).first()
        if reaction:
            if reaction.reaction == ReactionChoices.UPVOTE:
                reactable.upvotes -= 1
                reactable.save()
            elif reaction.reaction == ReactionChoices.DOWNVOTE:
                reactable.downvotes -= 1
                reactable.save()
            reaction.delete()

        return reactable

    @detail_route(methods=['POST'])
    def upvote(self, request, pk):
        reactable = self.upvote(request, pk, self.get_object())
        response = {
            'result': self.serializer_class(reactable).data
        }
        return Response(response)

    @detail_route(methods=['POST'])
    def downvote(self, request, pk):
        reactable = self.downvote(request, pk, self.get_object())
        response = {
            'result': self.serializer_class(reactable).data
        }
        return Response(response)

    @detail_route(methods=['POST'])
    def flag(self, request, pk):
        reactable = self.flag(request, pk, self.get_object())
        response = {
            'result': self.serializer_class(reactable).data
        }
        return Response(response)

    @detail_route(methods=['POST'])
    def unvote(self, request, pk):
        reactable = self.unvote(request, pk, self.get_object())
        response = {
            'result': self.serializer_class(reactable).data
        }
        return Response(response)

    @detail_route(methods=['POST'])
    def unflag(self, request, pk):
        reactable = self.unflag(request, pk, self.get_object())
        response = {
            'result': self.serializer_class(reactable).data
        }
        return Response(response)


class CommentViewSet(ReactableViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class PhotoViewSet(ReactableViewSet):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

