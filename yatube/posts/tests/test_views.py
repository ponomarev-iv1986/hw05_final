import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Follow, Group, Post
from ..views import POSTS_AMOUNT

User = get_user_model()

# Константа, указывающая сколько постов на второй
# странице при тестировании папгинатора
P2_POSTS_AMOUNT: int = 3

# Константа, указывающая сколько постов всего
# при тестировании пагинатора
ALL_POSTS_AMOUNT: int = POSTS_AMOUNT + P2_POSTS_AMOUNT

# Временная папка для медиа-файлов
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    """Тестирование страниц приложения Post."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='testuser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
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
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост',
            image=uploaded
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
        self.client.force_login(PostPagesTests.user)

    def test_pages_uses_correct_template(self):
        """
        Проверяем name:namespace во view-функциях.
        """
        template_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test_slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': 'testuser'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                args=(PostPagesTests.post.pk,)
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                args=(PostPagesTests.post.pk,)
            ): 'posts/create_post.html',
            reverse(
                'posts:post_create'
            ): 'posts/create_post.html'
        }
        for name, template in template_pages_names.items():
            with self.subTest(name=name):
                response = self.client.get(name)
                self.assertTemplateUsed(response, template)

    def test_post_detail_show_correct_context(self):
        """Проверяем контекст страницы post_detail."""
        response = self.client.get(
            reverse(
                'posts:post_detail',
                args=(PostPagesTests.post.pk,)
            )
        )
        post_context = response.context.get('post')
        self.assertEqual(post_context, PostPagesTests.post)

    def test_index_show_correct_context(self):
        """Проверяем контекст домашней страницы."""
        response = self.client.get(
            reverse(
                'posts:index'
            )
        )
        page_context = response.context.get('page_obj')
        post_context = page_context.object_list[0]
        self.assertEqual(post_context, PostPagesTests.post)

    def test_profile_show_correct_context(self):
        """Проверяем контекст страницы profile."""
        response = self.client.get(
            reverse(
                'posts:profile',
                args=(PostPagesTests.user.username,)
            )
        )
        page_context = response.context.get('page_obj')
        count = response.context.get('count')
        author = response.context.get('author')
        post_context = page_context.object_list[0]
        self.assertEqual(post_context, PostPagesTests.post)
        self.assertIsInstance(count, int)
        self.assertEqual(author, PostPagesTests.post.author)

    def test_group_posts_show_correct_context(self):
        """Проверяем контекст страницы group_posts."""
        response = self.client.get(
            reverse(
                'posts:group_list',
                args=(PostPagesTests.post.group.slug,)
            )
        )
        page_context = response.context.get('page_obj')
        group = response.context.get('group')
        post_context = page_context.object_list[0]
        self.assertEqual(post_context, PostPagesTests.post)
        self.assertEqual(group, PostPagesTests.group)

    def test_post_edit_show_correct_context(self):
        """Проверяем контекст страницы post_edit."""
        response = self.client.get(
            reverse(
                'posts:post_edit',
                args=(PostPagesTests.post.pk,)
            )
        )
        form_context = response.context.get('form')
        post_context = response.context.get('post')
        is_edit_context = response.context.get('is_edit')
        self.assertIsInstance(form_context, PostForm)
        self.assertEqual(post_context, PostPagesTests.post)
        self.assertEqual(is_edit_context, True)

    def test_post_create_show_correct_context(self):
        """Проверяем контекст страницы post_create."""
        response = self.client.get(
            reverse('posts:post_create')
        )
        form_context = response.context.get('form')
        self.assertIsInstance(form_context, PostForm)


class CacheTest(TestCase):
    """Тестирование cache."""

    def setUp(self):
        super().setUp
        self.user = User.objects.create(username='testuser')
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        self.client = Client()
        self.client.force_login(self.user)
        self.post = Post.objects.create(
            author=self.user,
            group=self.group,
            text='Тестовый пост'
        )

    def test_cache_home_page(self):
        """Проверяем cache для домашней страницы."""
        response_1 = self.client.get(
            reverse('posts:index')
        )
        content_1 = response_1.content
        self.post.delete()
        response_2 = self.client.get(
            reverse('posts:index')
        )
        content_2 = response_2.content
        cache.clear()
        response_3 = self.client.get(
            reverse('posts:index')
        )
        content_3 = response_3.content
        self.assertEqual(content_1, content_2)
        self.assertNotEqual(content_1, content_3)


class FollowsTest(TestCase):
    """Тестирование подписок."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='testuser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.client = Client()
        cls.client.force_login(FollowsTest.user)
        cls.post = Post.objects.create(
            author=FollowsTest.user,
            group=FollowsTest.group,
            text='Тестовый пост'
        )
        cls.user_2 = User.objects.create(username='testuser_2')
        cls.user_3 = User.objects.create(username='testuser_3')

    def setUp(self):
        super().setUp()
        self.client_1 = Client()
        self.client_1.force_login(FollowsTest.user)
        self.client_2 = Client()
        self.client_2.force_login(FollowsTest.user_2)
        self.client_3 = Client()
        self.client_3.force_login(FollowsTest.user_3)

    def test_follow(self):
        """
        Проверяем подписку авторизованного пользователя.
        """
        follows = Follow.objects.filter(
            user=FollowsTest.user_2
        ).count()
        self.client_2.get(
            reverse(
                'posts:profile_follow',
                args=(FollowsTest.user.username,)
            )
        )
        response = self.client_2.get(
            reverse('posts:follow_index')
        )
        page_context = response.context.get('page_obj')
        self.assertEqual(
            len(page_context.object_list),
            follows + FollowsTest.user.posts.count()
        )
        self.assertEqual(
            Follow.objects.filter(
                user=FollowsTest.user_2
            ).count(),
            follows + FollowsTest.user.posts.count()
        )

    def test_unfollow_(self):
        """
        Проверяем отписку авторизованного пользователя.
        """
        self.client_2.get(
            reverse(
                'posts:profile_follow',
                args=(FollowsTest.user.username,)
            )
        )
        follows = Follow.objects.filter(
            user=FollowsTest.user_2
        ).count()
        self.client_2.get(
            reverse(
                'posts:profile_unfollow',
                args=(FollowsTest.user.username,)
            )
        )
        response = self.client_2.get(
            reverse('posts:follow_index')
        )
        page_context = response.context.get('page_obj')
        self.assertEqual(
            len(page_context.object_list),
            follows - FollowsTest.user.posts.count()
        )
        self.assertEqual(
            Follow.objects.filter(
                user=FollowsTest.user_2
            ).count(),
            follows - FollowsTest.user.posts.count()
        )

    def test_new_post(self):
        """
        Проверяем что новая запись появилась в подписках.
        """
        self.client_2.get(
            reverse(
                'posts:profile_follow',
                args=(FollowsTest.user.username,)
            )
        )
        follows_user_2 = Post.objects.filter(
            author__following__user=FollowsTest.user_2
        ).count()
        follows_user_3 = Post.objects.filter(
            author__following__user=FollowsTest.user_3
        ).count()
        Post.objects.create(
            author=FollowsTest.user,
            group=FollowsTest.group,
            text='Второй тестовый пост'
        )
        self.assertEqual(Post.objects.count(), 2)
        self.assertEqual(
            Post.objects.filter(
                author__following__user=FollowsTest.user_2
            ).count(),
            follows_user_2 + 1
        )
        self.assertEqual(
            Post.objects.filter(
                author__following__user=FollowsTest.user_3
            ).count(),
            follows_user_3
        )


class PaginatorViewsTest(TestCase):
    """Тестирование пагинатора."""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create(username='testuser')
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        self.client = Client()
        self.client.force_login(self.user)
        self.posts = [
            Post.objects.create(
                author=self.user,
                group=self.group,
                text='Тестовый пост'
            ) for _ in range(ALL_POSTS_AMOUNT)
        ]

    def test_home_page(self):
        """Проверяем пагинатор для домашней страницы."""
        paginator = {
            reverse('posts:index'): POSTS_AMOUNT,
            reverse('posts:index') + '?page=2': P2_POSTS_AMOUNT,
        }
        for address, amount in paginator.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(
                    len(response.context['page_obj']),
                    amount
                )

    def test_group_list(self):
        """Проверяем пагинатор в группе."""
        paginator = {
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test_slug'}
            ): POSTS_AMOUNT,
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test_slug'}
            ) + '?page=2': P2_POSTS_AMOUNT
        }
        for address, amount in paginator.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(
                    len(response.context['page_obj']),
                    amount
                )

    def test_profile(self):
        """Проверяем пагинатор на странице профайла."""
        paginator = {
            reverse(
                'posts:profile',
                kwargs={'username': 'testuser'}
            ): POSTS_AMOUNT,
            reverse(
                'posts:profile',
                kwargs={'username': 'testuser'}
            ) + '?page=2': P2_POSTS_AMOUNT
        }
        for address, amount in paginator.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(
                    len(response.context['page_obj']),
                    amount
                )
