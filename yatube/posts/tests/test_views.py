import tempfile
from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post
from posts.models import Group
from posts.models import User
from posts.models import Follow
from django.conf import settings


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testman')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif')

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=uploaded
        )
        cls.post_id = cls.post.id

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_page_uses_correct_templates(self):
        '''Проверяем, что используються правильные шаблоны'''
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': 'test-slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.user}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post_id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post_id}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_correct_context(self):
        """ Проверяем, что в index передается правильный контекст:
        1. В context есть page_obj.
        2. Размер списка не равен нулю.
        3. Есть картинка.
        """
        response = self.guest_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertIn('page_obj', response.context.keys())
        self.assertNotEqual(len(response.context['page_obj']), 0)
        self.assertEqual(first_object.image, PostViewsTests.post.image)

    def test_group_list_page_correct_context(self):
        '''Проверяем, что в список постов передается правильный контекст '''
        response = self.guest_client.get(reverse('posts:group_list',
                                         kwargs={'slug': 'test-slug'}))
        first_object = response.context['page_obj'][0]
        self.assertEqual(response.context['group'], self.group)
        self.assertEqual(first_object.image, PostViewsTests.post.image)

    def test_profile_page_correct_context(self):
        '''Проверяем, что в profile передается правильный контекст'''
        response = self.authorized_client.get(reverse('posts:profile',
                                              kwargs={'username': self.user}))
        first_object = response.context['page_obj'][0]
        self.assertEqual(response.context['author'], self.post.author)
        self.assertEqual(first_object.image, PostViewsTests.post.image)

    def test_post_detail_page_correct_context(self):
        '''Проверяем, что в post_detail передается правильный контекст'''
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post_id})
        )
        first_object = response.context['post']
        self.assertEqual(response.context['post'].id, self.post_id)
        self.assertEqual(first_object.image, PostViewsTests.post.image)

    def test_post_edit_page_correct_context(self):
        '''Проверяем, что в post_edit передается правильный контекст'''
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post_id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_post_page_correct_context(self):
        '''Проверяем, что в create_post передается правильный контекст'''
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_paginator(self):
        '''Проверка работы Пагинатора'''
        for post in range(11):
            post = Post.objects.create(
                text=f'Тестовый текст {post}',
                author=self.user,
                group=self.group,
            )
        posturls_posts_page = [('', 10), ('?page=2', 2)]
        templates = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': self.user}),
        ]
        for postsurls, posts in posturls_posts_page:
            for page in templates:
                with self.subTest(page=page):
                    response = self.authorized_client.get(page + postsurls)
                    self.assertEqual(len(response.context['page_obj']), posts)

    def test_cache(self):
        cache.clear()
        content = (self.authorized_client.get(reverse('posts:index'))).content
        self.post.delete
        content2 = (self.authorized_client.get(reverse('posts:index'))).content
        self.assertEqual(content, content2)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_autor = User.objects.create(
            username='post_autor',
        )
        cls.post_follower = User.objects.create(
            username='post_follower',
        )
        cls.post = Post.objects.create(
            text='Подпишись на меня',
            author=cls.post_autor,
        )

    def setUp(self):
        cache.clear()
        self.author_client = Client()
        self.author_client.force_login(self.post_follower)
        self.follower_client = Client()
        self.follower_client.force_login(self.post_autor)

    def test_follow_on_user(self):
        """Проверка подписки на пользователя."""
        self.follower_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.post_follower}))
        follow = Follow.objects.all(
        ).filter(user=self.post_autor, author=self.post_follower).exists()
        self.assertEqual(follow, True)

    def test_unfollow_on_user(self):
        """Проверка отписки от пользователя."""
        Follow.objects.create(
            user=self.post_autor,
            author=self.post_follower)
        self.follower_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.post_follower}))
        follow = Follow.objects.all(
        ).filter(user=self.post_autor, author=self.post_follower).exists()
        self.assertEqual(follow, False)

    def test_follow_on_authors(self):
        """Проверка записей у тех кто подписан."""
        post = Post.objects.create(
            author=self.post_autor,
            text="Подпишись на меня")
        Follow.objects.create(
            user=self.post_follower,
            author=self.post_autor)
        response = self.author_client.get(
            reverse('posts:follow_index'))
        self.assertIn(post, response.context['page_obj'].object_list)

    def test_notfollow_on_authors(self):
        """Проверка записей у тех кто не подписан."""
        post = Post.objects.create(
            author=self.post_autor,
            text="Подпишись на меня")
        response = self.author_client.get(
            reverse('posts:follow_index'))
        self.assertNotIn(post, response.context['page_obj'].object_list)

    def test_follow_user_user(self):
        """Проверка подписки на себя."""
        self.author_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.post_follower}))
        follow = Follow.objects.all(
        ).filter(user=self.post_follower, author=self.post_follower).exists()
        self.assertEqual(follow, False)
