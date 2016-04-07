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


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def create(self, request, *args, **kwargs):
        """
        create the item
        ---
        request_serializer: CreateItemSerializer
        """

        serialized_data = CreateItemSerializer(data=request.data)
        if serialized_data.is_valid():
            item = Item.objects.filter(user=request.user, location=serialized_data.validated_data['location']).first()
            author = get_author(request.user)
            status = ItemStatusChoices.UNVERIFIED if author < Configurations.AUTO_VERIFICATION_REPUTATION else ItemStatusChoices.VERIFIED
            if not item:
                item = Item.objects.create(
                        latitude=serialized_data.validated_data['latitude'],
                        longitude=serialized_data.validated_data['longitude'],
                        title=serialized_data.validated_data['title'],
                        description=serialized_data.validated_data['description'],
                        author=author,
                        status=status,
                )
            return Response(self.serializer_class(item).data)
        else:
            return Response(serialized_data.errors, status=HTTP_400_BAD_REQUEST)

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
            rating = Rating.objects.filter(item=item, author__user=request.user).first()
            if rating:
                item.rating -= rating.rating
                item.rating += serialized_data.validated_data['rating']
                item.save()

                rating.rating = serialized_data.validated_data['rating']
                rating.save()
            else:
                rating = Rating.objects.create(
                        rating=serialized_data.validated_data['rating'],
                        item=item,
                        author=get_author(request.user),
                )
                item.rating += rating.rating
                item.save()

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
        reaction = Reaction.objects.filter(author__user=request.user).exclude(reaction=ReactionChoices.FLAG).first()
        if reaction:
            if reaction.reaction == ReactionChoices.DOWNVOTE:
                reactable.upvotes += 1
                reactable.downvotes -= 1
                reactable.recalculate_score()
                reactable.save()

            if reaction.reaction == ReactionChoices.NONE:
                reactable.upvotes += 1
                reactable.recalculate_score()
                reactable.save()

            reaction.reaction = ReactionChoices.UPVOTE
            reaction.save()

        else:
            Reaction.objects.create(
                    reaction=ReactionChoices.UPVOTE,
                    reactable=reactable,
                    author=get_author(request.user),
            )
            reactable.upvotes += 1
            reactable.recalculate_score()
            reactable.save()

        return reactable

    @staticmethod
    def handle_downvote(request, pk, reactable):
        reaction = Reaction.objects.filter(author__user=request.user).exclude(reaction=ReactionChoices.FLAG).first()
        if reaction:
            if reaction.reaction == ReactionChoices.UPVOTE:
                reactable.upvotes -= 1
                reactable.downvotes += 1
                reactable.recalculate_score()
                reactable.save()

            if reaction.reaction == ReactionChoices.NONE:
                reactable.downvotes += 1
                reactable.recalculate_score()
                reactable.save()

            reaction.reaction = ReactionChoices.DOWNVOTE
            reaction.save()

        else:
            Reaction.objects.create(
                    reaction=ReactionChoices.DOWNVOTE,
                    reactable=reactable,
                    author=get_author(request.user),
            )
            reactable.downvotes += 1
            reactable.recalculate_score()
            reactable.save()

        return reactable

    @staticmethod
    def handle_flag(request, pk, reactable):
        reaction = Reaction.objects.filter(author__user=request.user, reaction=ReactionChoices.FLAG).first()
        if not reaction:
            Reaction.objects.create(
                    reaction=ReactionChoices.FLAG,
                    reactable=reactable,
                    author=get_author(request.user),
            )
            reactable.flags += 1
            reactable.recalculate_score()
            reactable.save()

        return reactable

    @staticmethod
    def handle_unflag(request, pk, reactable):
        reaction = Reaction.objects.filter(author__user=request.user, reaction=ReactionChoices.FLAG).first()
        if reaction:
            reaction.delete()
            reactable.flags -= 1
            reactable.recalculate_score()
            reactable.save()

        return reactable

    @staticmethod
    def handle_unvote(request, pk, reactable):
        reaction = Reaction.objects.filter(author__user=request.user).exclude(reaction=ReactionChoices.FLAG).first()
        if reaction:
            if reaction.reaction == ReactionChoices.UPVOTE:
                reactable.upvotes -= 1
                reactable.recalculate_score()
                reactable.save()
            elif reaction.reaction == ReactionChoices.DOWNVOTE:
                reactable.downvotes -= 1
                reactable.recalculate_score()
                reactable.save()
            reaction.delete()

        return reactable

    @detail_route(methods=['POST'], permission_classes=[IsAuthenticated])
    def upvote(self, request, pk):
        """
        ---
        parameters_strategy:
            form: replace
        """

        reactable = self.handle_upvote(request, pk, self.get_object())
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
