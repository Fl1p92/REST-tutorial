from django.db import models

from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import get_all_lexers, get_lexer_by_name
from pygments.styles import get_all_styles

LEXERS = [item for item in get_all_lexers() if item[1]]
LANGUAGE_CHOICES = sorted([(item[1][0], item[0]) for item in LEXERS])
STYLE_CHOICES = sorted((item, item) for item in get_all_styles())


class Snippet(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100, blank=True, default='')
    code = models.TextField()
    linenos = models.BooleanField(default=False)
    language = models.CharField(choices=LANGUAGE_CHOICES, default='python', max_length=100)
    style = models.CharField(choices=STYLE_CHOICES, default='friendly', max_length=100)
    owner = models.ForeignKey('auth.User', related_name='snippets', on_delete=models.CASCADE)
    highlighted = models.TextField()

    def save(self, *args, **kwargs):
        """
        Use the `pygments` library to create a highlighted HTML representation of the code snippet.
        """
        lexer = get_lexer_by_name(self.language)
        linenos = 'table' if self.linenos else False
        options = {'title': self.title} if self.title else {}
        formatter = HtmlFormatter(style=self.style, linenos=linenos, full=True, **options)
        self.highlighted = highlight(self.code, lexer, formatter)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ('created',)

########################################################################################################################
######################################### New API ########################################################################
########################################################################################################################
class ContactsList(models.Model):
    owner = models.OneToOneField('auth.User', related_name='contacts_list', on_delete=models.CASCADE)


class ContactLine(models.Model):
    contacts_list = models.ForeignKey('ContactsList', on_delete=models.CASCADE, related_name='contact_lines')
    contact = models.ForeignKey('auth.User', on_delete=models.CASCADE)

    class Meta:
        unique_together = (
            ("contacts_list", "contact"),
        )


class Message(models.Model):
    create_time = models.DateTimeField('Create time', auto_now_add=True)
    text = models.TextField('Message text')
    author = models.ForeignKey('auth.User', related_name='messages', on_delete=models.SET_NULL, null=True)
    chat = models.ForeignKey('Chat', related_name='messages', on_delete=models.CASCADE)


class Chat(models.Model):
    title = models.CharField(max_length=100, blank=True, null=True)


class ChatUser(models.Model):
    chat = models.ForeignKey('Chat', on_delete=models.CASCADE, related_name='chat_users')
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)

    class Meta:
        unique_together = (
            ("chat", "user"),
        )
##########!!!!!!!! 2 app: contact, chat. !!!!!!############
# 1) url для api.

from django.urls import path

from rest_framework.urlpatterns import format_suffix_patterns

from . import views

urlpatterns = format_suffix_patterns([
    path('', views.api_root),
    path('users/', views.UserList.as_view(), name='user-list'),
    path('users/<int:pk>/', views.UserDetail.as_view(), name='user-detail'),
    path('users/<int:pk>/contacts/', views.UserContacts.as_view(), name='user-contacts'),

    path('chats/', views.ChatList.as_view(), name='chat-list'),
    path('chats/<int:pk>/', views.ChatDetail.as_view(), name='chat-detail'),
])


# 2) api point для user:
# - поиск всех кроме себя с пагинацией.

from django.contrib.auth.models import User

from rest_framework import generics
from .serializers import UserSerializer

class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            self.queryset = User.objects.exclude(username=self.request.user.username)
        return super().get_queryset()

# пагинация
# В settings:

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}
