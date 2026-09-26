"""
URL configuration for placement_tracker project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from accounts import views
from django.urls import path

urlpatterns = [
    path("", views.login, name="home"),
    path("admin/", admin.site.urls),
    path("register/", views.register, name="register"),
    path("login/", views.login, name="login"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/add-subject/", views.add_subject, name="add_subject"),
    path("subjects/<int:subject_id>/", views.subject_detail, name="subject_detail"),
    path("subjects/<int:subject_id>/add-topic/", views.add_topic, name="add_topic"),
    path("topics/<int:topic_id>/", views.topic_detail, name="topic_detail"),
    path(
        "topics/<int:topic_id>/add-question/", views.add_question, name="add_question"
    ),
    path(
        "questions/<int:question_id>/toggle-solved/",
        views.toggle_question_solved,
        name="toggle_question_solved",
    ),
    path(
        "questions/<int:question_id>/toggle-revision/",
        views.toggle_question_revision,
        name="toggle_question_revision",
    ),
    path("subjects/<int:subject_id>/add-note/", views.add_note, name="add_note"),
    path("notes/<int:note_id>/delete/", views.delete_note, name="delete_note"),
    path("notes/<int:note_id>/edit/", views.edit_note, name="edit_note"),
    path("revision/", views.revision, name="revision"),
    path("goals/", views.goals, name="goals"),
    path("goals/add/", views.add_goal, name="add_goal"),
    path(
        "subjects/<int:subject_id>/topics/",
        views.get_subject_topics,
        name="get_subject_topics",
    ),
    path("goals/delete/<int:goal_id>/", views.delete_goal, name="delete_goal"),
    path("goals/edit/<int:goal_id>/", views.edit_goal, name="edit_goal"),
    path("ai/chat/", views.ai_chat, name="ai_chat"),
]
