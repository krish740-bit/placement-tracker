import json
from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase, Client
from accounts.models import Subject, Topic, Question, Goal


class AIAddQuestionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="student@example.com",
            email="student@example.com",
            password="StrongPassword123!",
        )
        self.other_user = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="StrongPassword123!",
        )

        self.subject_dsa = Subject.objects.create(
            user=self.user, name="Data Structures"
        )
        self.subject_web = Subject.objects.create(
            user=self.user, name="Web Development"
        )

        self.topic_arrays = Topic.objects.create(
            subject=self.subject_dsa, name="Arrays"
        )
        self.topic_trees = Topic.objects.create(
            subject=self.subject_dsa, name="Trees"
        )

        # Other user's topic
        self.other_subject = Subject.objects.create(
            user=self.other_user, name="Other Subject"
        )
        self.other_topic = Topic.objects.create(
            subject=self.other_subject, name="Other Topic"
        )

        self.client = Client()
        self.client.login(username="student@example.com", password="StrongPassword123!")

    def test_unauthenticated_request_rejected(self):
        anonymous_client = Client()
        response = anonymous_client.post(
            "/ai/add-question/",
            data=json.dumps({"topic": "Arrays", "title": "Two Sum"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_rejected_non_post_requests(self):
        response = self.client.get("/ai/add-question/")
        self.assertEqual(response.status_code, 405)
        data = response.json()
        self.assertIn("error", data)

    def test_invalid_json_payload(self):
        response = self.client.post(
            "/ai/add-question/",
            data="not-a-valid-json{",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid JSON", response.json()["error"])

    def test_non_dict_json_payload(self):
        response = self.client.post(
            "/ai/add-question/",
            data=json.dumps(["Arrays", "Two Sum"]),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("JSON object", response.json()["error"])

    def test_missing_title_rejected(self):
        response = self.client.post(
            "/ai/add-question/",
            data=json.dumps({"topic": "Arrays", "title": "   "}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Question title cannot be empty", response.json()["error"])

    def test_title_length_limit(self):
        too_long_title = "A" * 201
        response = self.client.post(
            "/ai/add-question/",
            data=json.dumps({"topic": "Arrays", "title": too_long_title}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("200 characters", response.json()["error"])

    def test_missing_topic_and_topic_id_rejected(self):
        response = self.client.post(
            "/ai/add-question/",
            data=json.dumps({"title": "Two Sum"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Topic or topic ID is required", response.json()["error"])

    def test_topic_name_length_limit(self):
        too_long_topic = "T" * 101
        response = self.client.post(
            "/ai/add-question/",
            data=json.dumps({"topic": too_long_topic, "title": "Valid Title"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("100 characters", response.json()["error"])

    def test_invalid_field_types(self):
        response = self.client.post(
            "/ai/add-question/",
            data=json.dumps({"topic": 12345, "title": "Valid Title"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

        response2 = self.client.post(
            "/ai/add-question/",
            data=json.dumps({"topic": "Arrays", "title": ["Not a string"]}),
            content_type="application/json",
        )
        self.assertEqual(response2.status_code, 400)

    def test_invalid_url_rejected(self):
        response = self.client.post(
            "/ai/add-question/",
            data=json.dumps(
                {
                    "topic": "Arrays",
                    "title": "Two Sum",
                    "link": "javascript:alert('xss')",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid URL", response.json()["error"])

    def test_blank_url_allowed(self):
        response = self.client.post(
            "/ai/add-question/",
            data=json.dumps(
                {
                    "topic": "Arrays",
                    "title": "Two Sum No Link",
                    "link": "",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        q = Question.objects.get(id=data["question_id"])
        self.assertEqual(q.link, "")
        self.assertEqual(q.title, "Two Sum No Link")

    def test_valid_url_allowed(self):
        response = self.client.post(
            "/ai/add-question/",
            data=json.dumps(
                {
                    "topic": "Arrays",
                    "title": "Two Sum With Link",
                    "link": "https://leetcode.com/problems/two-sum/",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        q = Question.objects.get(id=data["question_id"])
        self.assertEqual(q.link, "https://leetcode.com/problems/two-sum/")

    def test_topic_not_found(self):
        response = self.client.post(
            "/ai/add-question/",
            data=json.dumps({"topic": "Nonexistent Topic", "title": "Sample Q"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("was not found", response.json()["error"])

    def test_unauthorized_topic_id(self):
        # Attempting to add a question using another user's topic ID
        response = self.client.post(
            "/ai/add-question/",
            data=json.dumps(
                {
                    "topic_id": self.other_topic.id,
                    "title": "Unauthorized Add",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            Question.objects.filter(title="Unauthorized Add").exists()
        )

    def test_ambiguous_topic_rejected(self):
        # Create an identically named topic under another subject for the same user
        Topic.objects.create(subject=self.subject_web, name="Arrays")

        response = self.client.post(
            "/ai/add-question/",
            data=json.dumps({"topic": "Arrays", "title": "Ambiguous Array Question"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Multiple topics named 'Arrays'", response.json()["error"])
        self.assertIn("Data Structures", response.json()["error"])
        self.assertIn("Web Development", response.json()["error"])

    def test_ambiguous_topic_disambiguated_by_subject(self):
        # Create an identically named topic under another subject for the same user
        Topic.objects.create(subject=self.subject_web, name="Arrays")

        response = self.client.post(
            "/ai/add-question/",
            data=json.dumps(
                {
                    "topic": "Arrays",
                    "subject": "Web Development",
                    "title": "JS Array Methods",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        q = Question.objects.get(id=data["question_id"])
        self.assertEqual(q.topic.subject.name, "Web Development")

    def test_successful_question_creation_by_name(self):
        response = self.client.post(
            "/ai/add-question/",
            data=json.dumps(
                {
                    "topic": "Trees",
                    "title": "Invert Binary Tree",
                    "link": "https://leetcode.com/problems/invert-binary-tree/",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("Invert Binary Tree", data["message"])
        self.assertEqual(data["topic_name"], "Trees")

        q = Question.objects.get(id=data["question_id"])
        self.assertEqual(q.topic, self.topic_trees)
        self.assertFalse(q.solved)
        self.assertFalse(q.needs_revision)

    def test_successful_question_creation_by_id(self):
        response = self.client.post(
            "/ai/add-question/",
            data=json.dumps(
                {
                    "topic_id": self.topic_arrays.id,
                    "title": "Subarray Sum Equals K",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        q = Question.objects.get(id=data["question_id"])
        self.assertEqual(q.topic, self.topic_arrays)


class AIChatTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="student@example.com",
            email="student@example.com",
            password="StrongPassword123!",
        )
        self.client = Client()
        self.client.login(username="student@example.com", password="StrongPassword123!")

    def test_unauthenticated_chat_rejected(self):
        anonymous = Client()
        response = anonymous.post(
            "/ai/chat/",
            data=json.dumps({"message": "Hello"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_non_post_chat_rejected(self):
        response = self.client.get("/ai/chat/")
        self.assertEqual(response.status_code, 405)

    def test_invalid_json_chat_rejected(self):
        response = self.client.post(
            "/ai/chat/",
            data="not-valid-json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_empty_message_chat_rejected(self):
        response = self.client.post(
            "/ai/chat/",
            data=json.dumps({"message": "   "}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Message cannot be empty", response.json()["error"])

    @patch("accounts.views.ask_gemini")
    def test_successful_chat_mocked(self, mock_ask):
        mock_ask.return_value = "Keep working on your Tree traversals!"
        response = self.client.post(
            "/ai/chat/",
            data=json.dumps({"message": "What should I practice?"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["reply"], "Keep working on your Tree traversals!"
        )


class LogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="student@example.com",
            email="student@example.com",
            password="StrongPassword123!",
        )
        self.client = Client()
        self.client.login(username="student@example.com", password="StrongPassword123!")

    def test_logout_get_rejected(self):
        # GET request to logout must be rejected with 405 Method Not Allowed
        response = self.client.get("/logout/")
        self.assertEqual(response.status_code, 405)

    def test_logout_post_successful(self):
        response = self.client.post("/logout/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)


class SubjectTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="student@example.com",
            email="student@example.com",
            password="StrongPassword123!",
        )
        self.client = Client()
        self.client.login(username="student@example.com", password="StrongPassword123!")

    def test_add_subject_unauthenticated_redirects_to_login(self):
        anonymous = Client()
        response = anonymous.post("/dashboard/add-subject/", data={"name": "Algorithms"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_add_subject_post_creates_subject_and_redirects(self):
        response = self.client.post("/dashboard/add-subject/", data={"name": "Algorithms"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/dashboard/")
        self.assertTrue(Subject.objects.filter(user=self.user, name="Algorithms").exists())

    def test_add_subject_get_redirects_to_dashboard(self):
        response = self.client.get("/dashboard/add-subject/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/dashboard/")

    def test_add_subject_unsupported_method_returns_405(self):
        response = self.client.put("/dashboard/add-subject/", data={"name": "Algorithms"})
        self.assertEqual(response.status_code, 405)


class RevisionToggleNavigationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="student@example.com",
            email="student@example.com",
            password="StrongPassword123!",
        )
        self.other_user = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="StrongPassword123!",
        )
        self.subject = Subject.objects.create(user=self.user, name="Data Structures")
        self.topic = Topic.objects.create(subject=self.subject, name="Graphs")
        self.question = Question.objects.create(
            topic=self.topic, title="Dijkstra Algorithm", needs_revision=True
        )

        self.other_subject = Subject.objects.create(user=self.other_user, name="Other")
        self.other_topic = Topic.objects.create(subject=self.other_subject, name="Other Topic")
        self.other_question = Question.objects.create(
            topic=self.other_topic, title="Other Question", needs_revision=True
        )

        self.client = Client()
        self.client.login(username="student@example.com", password="StrongPassword123!")

    def test_toggle_revision_from_revision_page_redirects_to_revision(self):
        response = self.client.post(
            f"/questions/{self.question.id}/toggle-revision/",
            data={"next": "/revision/"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/revision/")
        self.question.refresh_from_db()
        self.assertFalse(self.question.needs_revision)

    def test_toggle_revision_from_topic_detail_redirects_to_topic_detail(self):
        topic_url = f"/topics/{self.topic.id}/"
        response = self.client.post(
            f"/questions/{self.question.id}/toggle-revision/",
            data={"next": topic_url},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, topic_url)
        self.question.refresh_from_db()
        self.assertFalse(self.question.needs_revision)

    def test_toggle_revision_fallback_without_next(self):
        response = self.client.post(
            f"/questions/{self.question.id}/toggle-revision/"
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/topics/{self.topic.id}/")
        self.question.refresh_from_db()
        self.assertFalse(self.question.needs_revision)

    def test_toggle_revision_open_redirect_rejected(self):
        response = self.client.post(
            f"/questions/{self.question.id}/toggle-revision/",
            data={"next": "https://attacker.com/malicious"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/topics/{self.topic.id}/")

    def test_toggle_revision_referer_used_when_no_next(self):
        response = self.client.post(
            f"/questions/{self.question.id}/toggle-revision/",
            HTTP_REFERER="http://testserver/revision/",
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "http://testserver/revision/")

    def test_toggle_revision_get_does_not_mutate(self):
        response = self.client.get(
            f"/questions/{self.question.id}/toggle-revision/",
            data={"next": "/revision/"},
        )
        self.assertEqual(response.status_code, 302)
        self.question.refresh_from_db()
        self.assertTrue(self.question.needs_revision)

    def test_toggle_revision_unauthorized_question_404(self):
        response = self.client.post(
            f"/questions/{self.other_question.id}/toggle-revision/",
            data={"next": "/revision/"},
        )
        self.assertEqual(response.status_code, 404)


class EditGoalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="student@example.com",
            email="student@example.com",
            password="StrongPassword123!",
        )
        self.other_user = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="StrongPassword123!",
        )
        self.subject1 = Subject.objects.create(user=self.user, name="DSA")
        self.topic1 = Topic.objects.create(subject=self.subject1, name="Recursion")
        self.topic2 = Topic.objects.create(subject=self.subject1, name="Dynamic Programming")

        self.subject2 = Subject.objects.create(user=self.user, name="System Design")
        self.topic3 = Topic.objects.create(subject=self.subject2, name="Caching")

        self.other_subject = Subject.objects.create(user=self.other_user, name="Other Subject")
        self.other_topic = Topic.objects.create(subject=self.other_subject, name="Other Topic")

        self.goal = Goal.objects.create(
            user=self.user,
            title="Solve 10 Recursion Questions",
            target=10,
            subject=self.subject1,
            topic=self.topic1,
        )

        self.other_goal = Goal.objects.create(
            user=self.other_user,
            title="Other Goal",
            target=5,
        )

        self.client = Client()
        self.client.login(username="student@example.com", password="StrongPassword123!")

    def test_edit_goal_get_renders_preselected_values(self):
        response = self.client.get(f"/goals/edit/{self.goal.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="Solve 10 Recursion Questions"')
        self.assertContains(response, f'value="{self.subject1.id}"')
        self.assertContains(response, f'value="{self.topic1.id}"')
        self.assertContains(response, "selected")

    def test_edit_goal_change_subject_and_topic(self):
        response = self.client.post(
            f"/goals/edit/{self.goal.id}/",
            data={
                "title": "Master Caching",
                "target": "15",
                "subject": str(self.subject2.id),
                "topic": str(self.topic3.id),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/goals/")
        self.goal.refresh_from_db()
        self.assertEqual(self.goal.title, "Master Caching")
        self.assertEqual(self.goal.target, 15)
        self.assertEqual(self.goal.subject, self.subject2)
        self.assertEqual(self.goal.topic, self.topic3)

    def test_edit_goal_clear_subject_and_topic(self):
        response = self.client.post(
            f"/goals/edit/{self.goal.id}/",
            data={
                "title": "General Prep Goal",
                "target": "20",
                "subject": "",
                "topic": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/goals/")
        self.goal.refresh_from_db()
        self.assertEqual(self.goal.title, "General Prep Goal")
        self.assertIsNone(self.goal.subject)
        self.assertIsNone(self.goal.topic)

    def test_edit_goal_topic_must_belong_to_subject(self):
        # topic3 belongs to subject2, but subject1 is submitted
        response = self.client.post(
            f"/goals/edit/{self.goal.id}/",
            data={
                "title": "Invalid Topic Subject Pair",
                "target": "5",
                "subject": str(self.subject1.id),
                "topic": str(self.topic3.id),
            },
        )
        self.assertEqual(response.status_code, 404)

    def test_edit_goal_unauthorized_subject_404(self):
        response = self.client.post(
            f"/goals/edit/{self.goal.id}/",
            data={
                "title": "Hacked Goal",
                "target": "5",
                "subject": str(self.other_subject.id),
                "topic": "",
            },
        )
        self.assertEqual(response.status_code, 404)

    def test_edit_goal_unauthorized_goal_404(self):
        response = self.client.get(f"/goals/edit/{self.other_goal.id}/")
        self.assertEqual(response.status_code, 404)

    def test_get_subject_topics_api(self):
        response = self.client.get(f"/subjects/{self.subject1.id}/topics/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("topics", data)
        topic_names = [t["name"] for t in data["topics"]]
        self.assertIn("Recursion", topic_names)
        self.assertIn("Dynamic Programming", topic_names)

    def test_get_subject_topics_unauthorized_404(self):
        response = self.client.get(f"/subjects/{self.other_subject.id}/topics/")
        self.assertEqual(response.status_code, 404)
