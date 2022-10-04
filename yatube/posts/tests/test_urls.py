from django.test import TestCase, Client
from http import HTTPStatus
from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_name')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_exists_at_desired_location(self):
        """Общедоступные страницы сайта"""
        urls_response = (
            '/',
            '/group/test-slug/',
            '/profile/test_name/',
            f'/posts/{self.post.pk}/',
        )
        for url in urls_response:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)
