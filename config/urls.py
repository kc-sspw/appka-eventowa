from django.contrib import admin
from django.urls import path

from accounts import views as accounts
from events import views as events
from game import views as game
from media_storage import oauth

urlpatterns = [
    path("admin/", admin.site.urls),
    path("oauth/callback", oauth.callback),
    path("auth/login", accounts.login, name="login"),
    path("auth/logout", accounts.logout, name="logout"),
    path("", game.news),
    path("news", game.news, name="news"),
    path("information", game.information, name="information"),
    path("game", game.game, name="game"),
    path("game/draw", game.draw_view, name="draw"),
    path("assignments/<uuid:assignment_id>/photo", game.upload, name="upload"),
    path("gallery", game.gallery, name="gallery"),
    path("photos/<uuid:photo_id>", game.photo_detail, name="photo"),
    path("photos/<uuid:photo_id>/content", game.photo_content, name="photo_content"),
    path("photos/<uuid:photo_id>/thumbnail", game.photo_content, {"small": True}, name="thumbnail"),
    path("photos/<uuid:photo_id>/rating", game.rating, name="rating"),
    path("photos/<uuid:photo_id>/score", game.rating, {"organizer": True}, name="score"),
    path("photos/<uuid:photo_id>/comments", game.add_comment, name="comment"),
    path("comments/<uuid:comment_id>/delete", game.remove_comment, name="delete_comment"),
    path("organizer", events.organizer, name="organizer"),
    path("organizer/settings", events.settings_view, name="settings"),
    path("organizer/activate", events.activate, name="activate"),
    path("organizer/participants", events.participants, name="participants"),
    path("organizer/participants/new", events.participant_edit, name="participant_new"),
    path(
        "organizer/participants/<uuid:account_id>", events.participant_edit, name="participant_edit"
    ),
    path(
        "organizer/participants/<uuid:account_id>/reset",
        events.participant_reset,
        name="participant_reset",
    ),
    path("organizer/import", events.import_view, name="import"),
    path("organizer/imports", accounts.imports, name="imports"),
    path("organizer/storage/connect", oauth.start, name="storage_connect"),
    path("organizer/storage/finish", oauth.finish, name="storage_finish"),
    path("organizer/storage/check", events.storage_check, name="storage_check"),
    path("organizer/storage/<uuid:operation_id>/retry", events.retry, name="storage_retry"),
    path("organizer/photos/<uuid:photo_id>/delete", game.remove_photo, name="delete_photo"),
    path("organizer/close", events.close, name="close"),
    path("organizer/cleanup", events.cleanup, name="cleanup"),
    path("organizer/<str:kind>", events.entity_list, name="entity_list"),
    path("organizer/<str:kind>/new", events.edit, name="entity_new"),
    path("organizer/<str:kind>/<uuid:object_id>", events.edit, name="entity_edit"),
    path(
        "organizer/<str:kind>/<uuid:object_id>/delete", events.delete_entity, name="entity_delete"
    ),
]
