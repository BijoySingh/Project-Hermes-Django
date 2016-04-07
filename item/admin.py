from django.contrib import admin

# Register your models here.
from item.models import Item, Comment, Photo, Rating, Reaction


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'latitude', 'longitude', 'rating', 'author']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'comment', 'upvotes', 'downvotes', 'flags', 'author']


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ['id', 'picture', 'upvotes', 'downvotes', 'flags', 'author']


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'item', 'rating']


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'reactable', 'reaction']
