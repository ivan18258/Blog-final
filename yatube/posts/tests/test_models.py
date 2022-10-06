from cgitb import text
from django.test import TestCase

from posts.models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))

    def test_models_have_correct_object_names_group(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        expected_object_name = group.title[:15]
        self.assertEqual(expected_object_name, str(group))

    def test_title_label(self):
        """verbose_name поля title совпадает с ожидаемым."""
        verbose = Post._meta.get_field('text').verbose_name
        self.assertEqual('Текст поста', verbose)

    def test_title_help_text(self):
        """help_text поля text совпадает с ожидаемым."""
        help_text = Post._meta.get_field('text').help_text
        self.assertEqual('Введите текст поста', help_text)
