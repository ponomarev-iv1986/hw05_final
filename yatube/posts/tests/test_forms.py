import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

# Временная папка для медиа-файлов
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    """Тестирование формы публикации поста."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='testuser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост'
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            post=cls.post,
            text='Тестовый комментарий'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(
            TEMP_MEDIA_ROOT,
            ignore_errors=True
        )

    def setUp(self):
        super().setUp()
        self.client = Client()
        self.client.force_login(PostFormTests.user)
        self.guest_client = Client()

    def test_create_post(self):
        """Проверяем форму создания поста."""
        posts_count = Post.objects.count()
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
            content_type='image/gif'
        )
        form_data = {
            'text': 'Второй тестовый пост',
            'group': PostFormTests.group.pk,
            'image': uploaded,
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', args=('testuser',))
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Второй тестовый пост',
                group=PostFormTests.group.pk,
                author=PostFormTests.user,
            ).exists()
        )

    def test_edit_post(self):
        """Проверяем форму редактирования поста."""
        form_data = {
            'text': 'Измененный тестовый пост',
            'group': PostFormTests.group.pk,
        }
        response = self.client.post(
            reverse('posts:post_edit', args=(PostFormTests.post.pk,)),
            data=form_data
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args=(PostFormTests.post.pk,))
        )
        self.assertTrue(
            Post.objects.filter(
                text='Измененный тестовый пост',
                group=PostFormTests.group.pk,
                author=PostFormTests.user
            )
        )

    def test_add_comment_autorized_client(self):
        """Проверяем форму добавления комментария."""
        comments_count = Comment.objects.filter(
            post=PostFormTests.post
        ).count()
        form_data = {
            'text': 'Второй тестовый комментарий'
        }
        response = self.client.post(
            reverse(
                'posts:add_comment',
                args=(PostFormTests.post.pk,)
            ),
            data=form_data
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args=(PostFormTests.post.pk,))
        )
        self.assertEqual(
            Comment.objects.filter(
                post=PostFormTests.post
            ).count(), comments_count + 1
        )

    def test_add_comment_guest_client(self):
        """
        Проверяем редирект при комментировании гостем.
        """
        form_data = {
            'text': 'Второй тестовый комментарий'
        }
        response = self.guest_client.post(
            reverse(
                'posts:add_comment',
                args=(PostFormTests.post.pk,)
            ),
            data=form_data
        )
        self.assertRedirects(
            response,
            (
                '/auth/login/?next='
                + reverse(
                    'posts:add_comment',
                    args=(PostFormTests.post.pk,)
                )
            )
        )