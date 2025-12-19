from django.contrib import admin
from .models import Quiz, Question, Choice, Attempt, Answer

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2

class QuestionAdmin(admin.ModelAdmin):
    inlines = [ChoiceInline]

admin.site.register(Quiz)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Attempt)
admin.site.register(Answer)


# Register your models here.
