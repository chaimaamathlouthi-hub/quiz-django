from django.urls import path
from . import views

urlpatterns = [
    path("", views.quiz_list, name="quiz_list"),
    path("create/", views.quiz_create, name="quiz_create"),
    path("<int:quiz_id>/take/", views.take_quiz, name="take_quiz"),
    path("attempt/<int:attempt_id>/result/", views.quiz_result, name="quiz_result"),
    path("<int:quiz_id>/scores/", views.quiz_scores, name="quiz_scores"),
    path("register/", views.register, name="register"),
    path("<int:quiz_id>/questions/add/", views.question_add, name="question_add"),
    path("<int:quiz_id>/delete/", views.quiz_delete, name="quiz_delete"),
    path("create-full/", views.quiz_create_full, name="quiz_create_full"),




]
