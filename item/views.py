from django.shortcuts import get_object_or_404

# Create your views here.
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN

from account.models import UserProfile
from item.models import Item, Comment, Reaction, ReactionChoices, Photo, Rating, ItemStatusChoices
from item.serializers import CreateItemSerializer, ItemSerializer, BoundingBoxSerializer, CommentSerializer, \
    PhotoSerializer, UpdateItemSerializer, AddRatingSerializer, AddCommentSerializer, \
    AddPhotoSerializer
from project_hermes.hermes_config import Configurations


def get_author(user):
    return UserProfile.objects.filter(user=user).first()

def recalculate_reputation(profile: UserProfile):
    comments = Comment.objects.filter(author=profile)
    photos = Photo.objects.filter(author=profile)
    reactions = Reaction.objects.filter(author=profile).count()

    reputation = 0
    for comment in comments:
        reputation += comment.experience
    for photo in photos:
        reputation += photo.experience
    reputation += reactions

    items = Item.objects.filter(author=profile)
    for item in items:
        reputation += item.rating * 2
        reputation -= item.flags * 10

    profile.reputation = reputation
    profile.save()

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @staticmethod
    def is_valid_location(latitude, longitude):
        return -90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0

    def create(self, request, *args, **kwargs):
        """
        create the item
        ---
        request_serializer: CreateItemSerializer
        """

        serialized_data = CreateItemSerializer(data=request.data)
        if serialized_data.is_valid():
            latitude = serialized_data.validated_data['latitude']
            longitude = serialized_data.validated_data['longitude']

            if not self.is_valid_location(latitude, longitude):
                return Response({'success': False, 'message': 'Incorrect Location'}, status=HTTP_400_BAD_REQUEST)

            item = Item.objects.filter(author__user=request.user, longitude=longitude, latitude=latitude).first()
            author = get_author(request.user)
            status = ItemStatusChoices.UNVERIFIED if author.reputation < Configurations.AUTO_VERIFICATION_REPUTATION else ItemStatusChoices.VERIFIED
            if not item:
                item = Item.objects.create(
                        latitude=latitude,
                        longitude=longitude,
                        title=serialized_data.validated_data['title'],
                        description=serialized_data.validated_data['description'],
                        author=author,
                        status=status,
                )
            recalculate_reputation(author)
            return Response(self.serializer_class(item).data)
        else:
            return Response({'success': False, 'message': 'Incorrect Data Sent'}, status=HTTP_400_BAD_REQUEST)

    @list_route(methods=['POST'], permission_classes=[])
    def search_bounding_box(self, request):
        """
        Get items by Bounding Box
        ---
        request_serializer: BoundingBoxSerializer
        """

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
    def get_comments(self, request, pk):
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
        """
        update the item
        ---
        request_serializer: UpdateItemSerializer
        """

        serialized_data = UpdateItemSerializer(data=request.data)
        item = self.get_object()
        if item.author.user != request.user:
            return Response({'success': False, 'message': 'Unauthorized Access'}, status=HTTP_403_FORBIDDEN)

        if serialized_data.is_valid():
            item.title = serialized_data.validated_data['title']
            item.description = serialized_data.validated_data['description']
            item.save()
            recalculate_reputation(item.author)
            return Response(self.serializer_class(item).data)
        else:
            return Response({'success': False, 'message': 'Incorrect Data Sent'}, status=HTTP_400_BAD_REQUEST)

    @detail_route(methods=['POST'], permission_classes=[IsAuthenticated])
    def add_rating(self, request, pk):
        """
        Set rating of the item
        ---
        request_serializer: AddRatingSerializer
        """

        item = self.get_object()
        serialized_data = AddRatingSerializer(data=request.data)
        if serialized_data.is_valid():

            if not (0.0 <= serialized_data.validated_data['rating'] <= 5.0):
                return Response({'success': False, 'message': 'Incorrect Rating'}, status=HTTP_400_BAD_REQUEST)

            rating = Rating.objects.filter(item=item, author__user=request.user).first()
            if rating:
                rating.rating = serialized_data.validated_data['rating']
                rating.save()

                item.recalculate_rating()
                item.save()
            else:
                rating = Rating.objects.create(
                        rating=serialized_data.validated_data['rating'],
                        item=item,
                        author=get_author(request.user),
                )

                item.recalculate_rating()
                item.save()
            recalculate_reputation(rating.author)
            response = {
                'success': True,
                'result': self.serializer_class(item).data
            }
            return Response(response)
        else:
            return Response({'success': False, 'message': 'Incorrect Data Sent'}, status=HTTP_400_BAD_REQUEST)

    @detail_route(methods=['POST'], permission_classes=[IsAuthenticated])
    def add_comment(self, request, pk):
        """
        add comment of the item
        ---
        request_serializer: AddCommentSerializer
        """

        item = self.get_object()
        serialized_data = AddCommentSerializer(data=request.data)
        if serialized_data.is_valid():
            comment = Comment.objects.filter(item=item, author__user=request.user).first()
            if comment:
                comment.description = serialized_data.validated_data['description']
                comment.save()
            else:
                comment = Comment.objects.create(
                        description=serialized_data.validated_data['description'],
                        item=item,
                        author=get_author(request.user),
                )
            response = {
                'success': True,
                'result': CommentSerializer(comment).data
            }
            recalculate_reputation(comment.author)
            return Response(response)
        else:
            return Response({'success': False, 'message': 'Incorrect Data Sent'}, status=HTTP_400_BAD_REQUEST)

    @detail_route(methods=['POST'], permission_classes=[IsAuthenticated])
    def add_photo(self, request, pk):
        """
        add comment of the item
        ---
        request_serializer: AddPhotoSerializer
        """

        item = self.get_object()
        serialized_data = AddPhotoSerializer(data=request.data)
        if serialized_data.is_valid():
            photo = Photo.objects.filter(item=item, author__user=request.user).first()
            if photo:
                photo.description = serialized_data.validated_data['picture']
                photo.save()
            else:
                photo = Photo.objects.create(
                        picture=serialized_data.validated_data['picture'],
                        item=item,
                        author=get_author(request.user),
                )
            recalculate_reputation(photo.author)
            response = {
                'success': True,
                'result': PhotoSerializer(photo).data
            }
            return Response(response)
        else:
            return Response({'success': False, 'message': 'Incorrect Data Sent'}, status=HTTP_400_BAD_REQUEST)


class ReactableViewSet(viewsets.ModelViewSet):
    @staticmethod
    def handle_upvote(request, pk, reactable):
        reaction = Reaction.objects.filter(author__user=request.user, reactable=reactable) \
            .exclude(reaction=ReactionChoices.FLAG).first()
        if reaction:
            reaction.reaction = ReactionChoices.UPVOTE
            reaction.save()
        else:
            Reaction.objects.create(
                    reaction=ReactionChoices.UPVOTE,
                    reactable=reactable,
                    author=get_author(request.user),
            )

        reactable.recalculate_votes()
        reactable.recalculate_score()
        reactable.save()

        return reactable

    @staticmethod
    def handle_downvote(request, pk, reactable):
        reaction = Reaction.objects.filter(author__user=request.user, reactable=reactable) \
            .exclude(reaction=ReactionChoices.FLAG).first()
        if reaction:
            reaction.reaction = ReactionChoices.DOWNVOTE
            reaction.save()

        else:
            Reaction.objects.create(
                    reaction=ReactionChoices.DOWNVOTE,
                    reactable=reactable,
                    author=get_author(request.user),
            )

        reactable.recalculate_votes()
        reactable.recalculate_score()
        reactable.save()

        return reactable

    @staticmethod
    def handle_flag(request, pk, reactable):
        reaction = Reaction.objects.filter(author__user=request.user, reactable=reactable,
                                           reaction=ReactionChoices.FLAG).first()
        if not reaction:
            Reaction.objects.create(
                    reaction=ReactionChoices.FLAG,
                    reactable=reactable,
                    author=get_author(request.user),
            )

        reactable.recalculate_votes()
        reactable.recalculate_score()
        reactable.save()

        return reactable

    @staticmethod
    def handle_unflag(request, pk, reactable):
        reaction = Reaction.objects.filter(author__user=request.user, reactable=reactable,
                                           reaction=ReactionChoices.FLAG).first()
        if reaction:
            reaction.delete()

        reactable.recalculate_votes()
        reactable.recalculate_score()
        reactable.save()

        return reactable

    @staticmethod
    def handle_unvote(request, pk, reactable):
        reaction = Reaction.objects.filter(author__user=request.user, reactable=reactable) \
            .exclude(reaction=ReactionChoices.FLAG).first()
        if reaction:
            reaction.delete()

        reactable.recalculate_votes()
        reactable.recalculate_score()
        reactable.save()

        return reactable

    @detail_route(methods=['POST'], permission_classes=[IsAuthenticated])
    def upvote(self, request, pk):
        """
        ---
        parameters_strategy:
            form: replace
        """

        reactable = self.handle_upvote(request, pk, self.get_object())
        recalculate_reputation(reactable.author)
        recalculate_reputation(request.user)
        response = {
            'result': self.serializer_class(reactable).data
        }
        return Response(response)

    @detail_route(methods=['POST'], permission_classes=[IsAuthenticated])
    def downvote(self, request, pk):
        """
        ---
        parameters_strategy:
            form: replace
        """

        reactable = self.handle_downvote(request, pk, self.get_object())
        recalculate_reputation(reactable.author)
        recalculate_reputation(request.user)
        response = {
            'result': self.serializer_class(reactable).data
        }
        return Response(response)

    @detail_route(methods=['POST'], permission_classes=[IsAuthenticated])
    def flag(self, request, pk):
        """
        ---
        parameters_strategy:
            form: replace
        """

        reactable = self.handle_flag(request, pk, self.get_object())
        recalculate_reputation(reactable.author)
        recalculate_reputation(request.user)
        response = {
            'result': self.serializer_class(reactable).data
        }
        return Response(response)

    @detail_route(methods=['POST'], permission_classes=[IsAuthenticated])
    def unvote(self, request, pk):
        """
        ---
        parameters_strategy:
            form: replace
        """

        reactable = self.handle_unvote(request, pk, self.get_object())
        recalculate_reputation(reactable.author)
        recalculate_reputation(request.user)
        response = {
            'result': self.serializer_class(reactable).data
        }
        return Response(response)

    @detail_route(methods=['POST'], permission_classes=[IsAuthenticated])
    def unflag(self, request, pk):
        """
        ---
        parameters_strategy:
            form: replace
        """

        reactable = self.handle_unflag(request, pk, self.get_object())
        recalculate_reputation(reactable.author)
        recalculate_reputation(request.user)
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
