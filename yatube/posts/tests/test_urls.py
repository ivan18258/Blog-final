from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from posts.models import Group, Post


User = get_user_model()


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
        urls_response = {
            '/': 200,
            '/group/test-slug/': 200,
            '/profile/test_name/': 200,
            f'/posts/{self.post.pk}/': 200,
            '/unexisting_page/': 404,
        }
        for url, status_code in urls_response.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, status_code)
        