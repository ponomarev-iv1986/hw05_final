from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    """Тестирование URL приложения Post."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='testuser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовой описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост'
        )

    def setUp(self):
        super().setUp()
        self.guest_client = Client()
        self.autorized_client = Client()
        self.autorized_client.force_login(PostURLTests.user)

    def test_urls_guest_client_access(self):
        """Проверяем общедоступные страницы."""
        guest_urls = [
            '/',
            '/group/test_slug/',
            '/profile/testuser/',
            '/posts/1/',
        ]
        for page in guest_urls:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK
                )

    def test_urls_guest_unexisting_page(self):
        """Проверяем несуществующую страницу."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(
            response.status_code,
            HTTPStatus.NOT_FOUND
        )

    def test_urls_guest_redirect_post_edit(self):
        """
        Проверяем редирект со страницы редактирования поста.
        """
        response = self.guest_client.get(
            '/posts/1/edit',
            follow=True
        )
        self.assertRedirects(
            response,
            expected_url=('/auth/login/?next=/posts/1/edit/'),
            status_code=HTTPStatus.MOVED_PERMANENTLY
        )

    def test_urls_guest_redirect_post_create(self):
        """
        Проверяем редирект со страницы добавления поста.
        """
        response = self.guest_client.get(
            '/create/',
            follow=True
        )
        self.assertRedirects(
            response,
            ('/auth/login/?next=/create/')
        )

    def test_urls_autorized_client_access(self):
        """
        Проверяем доступность страниц для авторизованного пользователя.
        """
        autorized_urls = [
            '/',
            '/group/test_slug/',
            '/profile/testuser/',
            '/posts/1/',
            '/posts/1/edit/',
            '/create/',
        ]
        for page in autorized_urls:
            with self.subTest(page=page):
                response = self.autorized_client.get(
                    page
                )
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK
                )

    def test_urls_uses_correct_template(self):
        """
        Проверяем вызываемые HTML-шаблоны.
        """
        template_urls_name = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/profile/testuser/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in template_urls_name.items():
            with self.subTest(address=address):
                response = self.autorized_client.get(address)
                self.assertTemplateUsed(response, template)
