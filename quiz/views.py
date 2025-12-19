from django import forms
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib import messages
from .models import Quiz, Question, Choice, Attempt, Answer
from .forms import RegisterForm


# ===============================
# LISTE + CRÉATION DE QUIZ
# ===============================

@login_required
def quiz_list(request):
    quizzes = Quiz.objects.all()
    return render(request, "quiz/quiz_list.html", {"quizzes": quizzes})


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ["title", "description"]


@login_required
def quiz_create(request):
    if request.method == "POST":
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.created_by = request.user
            quiz.save()
            return redirect("quiz_list")
    else:
        form = QuizForm()

    return render(request, "quiz/quiz_create.html", {"form": form})


# ===============================
# PASSER QUIZ + RÉSULTATS + SCORES
# ===============================

@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.prefetch_related("choices").all()

    if request.method == "POST":
        attempt = Attempt.objects.create(
            quiz=quiz,
            user=request.user,
            completed_at=timezone.now()
        )

        score = 0
        for q in questions:
            choice_id = request.POST.get(f"question_{q.id}")
            if not choice_id:
                continue

            choice = get_object_or_404(Choice, id=choice_id, question=q)

            Answer.objects.create(
                attempt=attempt,
                question=q,
                selected_choice=choice
            )

            if choice.is_correct:
                score += 1

        attempt.score = score
        attempt.save()
        return redirect("quiz_result", attempt_id=attempt.id)

    return render(request, "quiz/take_quiz.html", {
        "quiz": quiz,
        "questions": questions
    })


@login_required
def quiz_result(request, attempt_id):
    attempt = get_object_or_404(
        Attempt.objects.select_related("quiz").prefetch_related(
            "answers__question",
            "answers__selected_choice",
            "quiz__questions__choices",
        ),
        id=attempt_id,
        user=request.user,
    )

    selected_map = {
        a.question_id: a.selected_choice_id
        for a in attempt.answers.all()
    }

    return render(request, "quiz/quiz_result.html", {
        "attempt": attempt,
        "quiz": attempt.quiz,
        "selected_map": selected_map,
    })


@login_required
def quiz_scores(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    attempts = (
        Attempt.objects
        .filter(quiz=quiz)
        .select_related("user")
        .order_by("-score", "completed_at")
    )

    return render(request, "quiz/quiz_scores.html", {
        "quiz": quiz,
        "attempts": attempts
    })


# ===============================
# INSCRIPTION
# ===============================

def register(request):
    if request.user.is_authenticated:
        return redirect("quiz_list")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("quiz_list")
    else:
        form = RegisterForm()

    return render(request, "registration/register.html", {"form": form})


# ===============================
# QUESTIONS
# ===============================

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["text"]


@login_required
def question_add(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            q = form.save(commit=False)
            q.quiz = quiz
            q.save()
            return redirect("question_add", quiz_id=quiz.id)
    else:
        form = QuestionForm()

    questions = quiz.questions.all()

    return render(request, "quiz/question_add.html", {
        "quiz": quiz,
        "form": form,
        "questions": questions,
    })


# ===============================
# CHOIX
# ===============================

class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ["text", "is_correct"]


@login_required
def choice_add(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    quiz = question.quiz

    if request.method == "POST":
        form = ChoiceForm(request.POST)
        if form.is_valid():
            choice = form.save(commit=False)
            choice.question = question

            # une seule bonne réponse
            if choice.is_correct:
                Choice.objects.filter(question=question).update(is_correct=False)

            choice.save()
            return redirect("choice_add", question_id=question.id)
    else:
        form = ChoiceForm()

    choices = question.choices.all()

    return render(request, "quiz/choice_add.html", {
        "quiz": quiz,
        "question": question,
        "form": form,
        "choices": choices,
    })
@login_required
def quiz_delete(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.method == "POST":
        quiz.delete()
        return redirect("quiz_list")

    return render(request, "quiz/quiz_delete.html", {
        "quiz": quiz
    })
from django.contrib import messages

@login_required
def quiz_create_full(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()

        if not title:
            messages.error(request, "Le titre est obligatoire.")
            return render(request, "quiz/quiz_create_full.html")

        quiz = Quiz.objects.create(
            title=title,
            description=description,
            created_by=request.user
        )

        # On lit les questions envoyées
        # question_count = nombre de blocs question créés par JS
        question_count = int(request.POST.get("question_count", "0") or "0")

        for i in range(question_count):
            q_text = request.POST.get(f"q_{i}_text", "").strip()
            if not q_text:
                continue

            question = Question.objects.create(quiz=quiz, text=q_text)

            # choix_count : nombre de choix dans cette question
            choice_count = int(request.POST.get(f"q_{i}_choice_count", "0") or "0")
            correct_index = request.POST.get(f"q_{i}_correct", None)  # ex "2"

            for j in range(choice_count):
                c_text = request.POST.get(f"q_{i}_c_{j}", "").strip()
                if not c_text:
                    continue

                is_correct = (correct_index is not None and str(j) == str(correct_index))
                Choice.objects.create(question=question, text=c_text, is_correct=is_correct)

        return redirect("quiz_list")

    return render(request, "quiz/quiz_create_full.html")
