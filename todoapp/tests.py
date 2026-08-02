from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from .models import Task


class DashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='secret123')
        self.other_user = User.objects.create_user(username='bob', password='secret123')
        self.task = Task.objects.create(
            user=self.user,
            title='Buy groceries',
            description='Milk and bread',
            due_date='2026-08-10',
            priority='High',
        )
        Task.objects.create(
            user=self.other_user,
            title='Other task',
            description='Someone else task',
            due_date='2026-08-11',
            priority='Low',
        )

    def test_dashboard_shows_current_user_profile_and_tasks(self):
        self.client.login(username='alice', password='secret123')
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome, alice!')
        self.assertContains(response, 'Buy groceries')
        self.assertNotContains(response, 'Other task')

    def test_dashboard_can_add_complete_and_delete_tasks(self):
        self.client.login(username='alice', password='secret123')

        response = self.client.post(reverse('dashboard'), {
            'action': 'add',
            'title': 'Study Django',
            'description': 'Complete chapter 1',
            'due_date': '2026-08-15',
            'priority': 'Medium',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Task.objects.filter(user=self.user, title='Study Django').exists())

        task = Task.objects.get(user=self.user, title='Study Django')
        response = self.client.post(reverse('dashboard'), {'action': 'complete', 'task_id': task.id})
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertTrue(task.completed)

        response = self.client.post(reverse('dashboard'), {'action': 'delete', 'task_id': task.id})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Task.objects.filter(id=task.id).exists())

    def test_registration_accepts_email_and_creates_user(self):
        response = self.client.post(reverse('register'), {
            'username': 'carol',
            'email': 'carol@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })

        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='carol')
        self.assertEqual(user.email, 'carol@example.com')

    def test_password_reset_page_renders(self):
        response = self.client.get(reverse('reset_password'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Forget Your Password')

    def test_forgot_password_sends_reset_email(self):
        self.user.email = 'alice@example.com'
        self.user.save(update_fields=['email'])

        response = self.client.post(reverse('forgot_password'), {'email': 'alice@example.com'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A password reset link has been sent to your email.')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Password reset request', mail.outbox[0].subject)
        self.assertIn('/reset/', mail.outbox[0].body)
