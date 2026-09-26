from django.contrib import admin
from .models import Subject , Topic, Question, Note

admin.site.register(Subject)
admin.site.register(Topic)
admin.site.register(Question)
admin.site.register(Note)