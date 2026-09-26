from django.contrib.auth.models import User
from django.db import models


class Subject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Topic(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Question(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    link = models.URLField(blank=True)
    solved = models.BooleanField(default=False)
    needs_revision = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Note(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    content = models.TextField()

    def __str__(self):
        return self.title


class Goal(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    title = models.CharField(max_length=200)

    target = models.PositiveIntegerField(default=1)

    completed = models.PositiveIntegerField(default=0)

    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, null=True, blank=True
    )

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
