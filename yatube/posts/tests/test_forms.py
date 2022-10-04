import shutil
import tempfile
from django import forms
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Group, Post, User, Comment


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
NEW_POST = reverse('posts:post_create')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TasCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.user_coment = User.objects.create_user(username='user_coment')
        cls.group = Group.objects.create(
            title='Test',
            slug='Tests',
            description='Testss'
        )
        cls.group2 = Group.objects.create(
            title='Test2',
            slug='Tests2',
            description='Testss2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='test text',
            group=cls.group
        )
        cls.post_id = cls.post.id
        cls.POST_URL = reverse(
            'posts:post_detail',
            args=[cls.post.id])
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit',
            args=[cls.post.id])
        cls.PROFILE_URL = reverse(
            'posts:profile',
            args=[cls.user.username]
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif')

    def test_post_create(self):
        """Создание поста."""
        posts = Post.objects.all()
        posts.delete()
        data = {
            'text': 'Текст формы',
            'group': self.group.id,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            NEW_POST,
            data=data,
            follow=True
        )
        post = response.context['page_obj'][0]
        self.assertEqual(len(response.context['page_obj']), 1)
        self.assertEqual(post.text, data['text'])
        self.assertEqual(data['group'], post.group.id)
        self.assertEqual(post.author, self.user)

        self.assertRedirects(response, self.PROFILE_URL)

    def test_new_post_show_correct_context(self):
        """Проверка контекста"""
        urls = [
            NEW_POST,
            self.POST_EDIT_URL
        ]
        form_fields = {'text': forms.fields.CharField,
                       'group': forms.fields.Field,
                       'image': forms.fields.Field,
                       }
        for url in urls:
            response = self.authorized_client.get(url)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_edit_post(self):
        """Проверка изменения и сохранения поста"""
        form_data = {
            'text': 'hi!',
            'group': self.post.group.id,
            'image': self.uploaded,
        }
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True,
        )
        post = response.context['post']
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(form_data['group'], post.group.id)
        self.assertEqual(post.author, self.post.author)
        self.assertRedirects(response, self.POST_URL)
        self.authorized_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True)
        post_with_image = Post.objects.get(text='hi!')
        self.assertEqual(
            Post.objects.count(), posts_count
        )
        self.assertEqual(
            post_with_image.text, form_data['text']
        )
        self.assertEqual(
            post_with_image.group.id, form_data['group']
        )
        self.assertIn(
            form_data['image'].name, post_with_image.image.name
        )

    def test_comment(self):
        """Проверка коментирования"""
        form_data = {
            'text': 'Привет',
        }
        posts_count = Comment.objects.count()
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post_id}),
            data=form_data,
        )
        comment = Comment.objects.get(text='Привет')
        self.assertEqual(
            Comment.objects.count(), posts_count + 1
        )
        self.assertEqual(
            comment.text, form_data['text']
        )
