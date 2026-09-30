from .models import Subject, Topic, Question, Note, Goal


def build_user_context(user):
    subjects = Subject.objects.filter(user=user)

    context = []

    total_questions = 0
    total_solved = 0
    total_revision = 0

    # -------------------------
    # OVERALL PROGRESS
    # -------------------------

    for subject in subjects:

        topics = Topic.objects.filter(subject=subject)

        for topic in topics:

            questions = Question.objects.filter(topic=topic)

            total_questions += questions.count()
            total_solved += questions.filter(solved=True).count()
            total_revision += questions.filter(needs_revision=True).count()

    context.append("=== OVERALL PROGRESS ===")

    context.append(f"Total questions: {total_questions}")

    context.append(f"Total solved: {total_solved}")

    context.append(f"Total marked for revision: {total_revision}")

    # -------------------------
    # SUBJECTS & TOPICS
    # -------------------------

    context.append("\n=== SUBJECT / TOPIC PROGRESS ===")

    for subject in subjects:

        context.append(f"\nSubject: {subject.name}")

        topics = Topic.objects.filter(subject=subject)

        for topic in topics:

            questions = Question.objects.filter(topic=topic)

            total = questions.count()
            solved = questions.filter(solved=True).count()

            revision = questions.filter(needs_revision=True).count()

            context.append(
                f"Topic: {topic.name} | "
                f"Total: {total} | "
                f"Solved: {solved} | "
                f"Revision: {revision}"
            )

    # -------------------------
    # REVISION QUEUE
    # -------------------------

    context.append("\n=== REVISION QUEUE ===")

    revision_questions = Question.objects.filter(
        topic__subject__user=user, needs_revision=True
    )

    if revision_questions.exists():

        for question in revision_questions:

            context.append(
                f"Question: {question.title} | "
                f"Topic: {question.topic.name} | "
                f"Solved: {question.solved}"
            )

    else:

        context.append("No questions currently marked for revision.")

    # -------------------------
    # GOALS
    # -------------------------

    context.append("\n=== GOALS ===")

    goals = Goal.objects.filter(user=user)

    if goals.exists():

        for goal in goals:

            if goal.topic:

                questions = Question.objects.filter(
                    topic=goal.topic, topic__subject__user=user
                )

                scope = f"Topic: {goal.topic.name}"

            elif goal.subject:

                questions = Question.objects.filter(
                    topic__subject=goal.subject, topic__subject__user=user
                )

                scope = f"Subject: {goal.subject.name}"

            else:

                questions = Question.objects.filter(topic__subject__user=user)

                scope = "All tracked subjects"

            completed = questions.filter(solved=True).count()

            remaining = max(goal.target - completed, 0)

            context.append(
                f"Goal: {goal.title} | "
                f"Scope: {scope} | "
                f"Completed: {completed} | "
                f"Target: {goal.target} | "
                f"Remaining: {remaining}"
            )

    else:

        context.append("No goals created.")

    # -------------------------
    # NOTES
    # -------------------------

    context.append("\n=== NOTES ===")

    notes = Note.objects.filter(user=user)

    if notes.exists():

        for note in notes:

            context.append(f"{note.title}: " f"{note.content[:500]}")

    else:

        context.append("No notes available.")

    return "\n".join(context)


def build_page_context(user, page, object_id=None):

    if page == "dashboard":

        subjects = Subject.objects.filter(user=user)

        context = ["CURRENT PAGE: DASHBOARD"]

        for subject in subjects:
            context.append(f"Subject: {subject.name}")

        return "\n".join(context)

    if page == "subject" and object_id:

        subject = Subject.objects.filter(id=object_id, user=user).first()

        if not subject:
            return "CURRENT PAGE: Subject not found."

        context = [f"CURRENT PAGE: SUBJECT", f"Subject: {subject.name}"]

        topics = Topic.objects.filter(subject=subject)

        for topic in topics:

            questions = Question.objects.filter(topic=topic)

            context.append(
                f"Topic: {topic.name} | "
                f"Questions: {questions.count()} | "
                f"Solved: {questions.filter(solved=True).count()} | "
                f"Revision: {questions.filter(needs_revision=True).count()}"
            )

        return "\n".join(context)

    if page == "topic" and object_id:

        topic = Topic.objects.filter(id=object_id, subject__user=user).first()

        if not topic:
            return "CURRENT PAGE: Topic not found."

        context = [
            "CURRENT PAGE: TOPIC",
            f"Subject: {topic.subject.name}",
            f"Topic: {topic.name}",
        ]

        questions = Question.objects.filter(topic=topic)

        for question in questions:

            context.append(
                f"Question: {question.title} | "
                f"Solved: {question.solved} | "
                f"Revision: {question.needs_revision}"
            )

        return "\n".join(context)

    if page == "revision":

        questions = Question.objects.filter(
            topic__subject__user=user, needs_revision=True
        )

        context = ["CURRENT PAGE: REVISION QUEUE"]

        for question in questions:

            context.append(
                f"Question: {question.title} | "
                f"Topic: {question.topic.name} | "
                f"Solved: {question.solved}"
            )

        return "\n".join(context)

    if page == "goals":

        goals = Goal.objects.filter(user=user)

        context = ["CURRENT PAGE: GOALS"]

        for goal in goals:

            if goal.topic:

                questions = Question.objects.filter(
                    topic=goal.topic, topic__subject__user=user
                )

                scope = f"Topic: {goal.topic.name}"

            elif goal.subject:

                questions = Question.objects.filter(
                    topic__subject=goal.subject, topic__subject__user=user
                )

                scope = f"Subject: {goal.subject.name}"

            else:

                questions = Question.objects.filter(topic__subject__user=user)

                scope = "All tracked subjects"

            completed = questions.filter(solved=True).count()

            context.append(
                f"Goal: {goal.title} | "
                f"Scope: {scope} | "
                f"Completed: {completed} | "
                f"Target: {goal.target}"
            )

        return "\n".join(context)

    return "CURRENT PAGE: General Placement Tracker page."
