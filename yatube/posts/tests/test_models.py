from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import POST_STR_AMOUNT, Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    """Тестирование модели Post."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='testuser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug_01',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text=('Тестовый пост ' * 10)
        )

    def test_models_have_correct_object_names(self):
        """
        Проверяем, что у моделей корректно работает __str__.
        """
        post = PostModelTest.post
        group = PostModelTest.group
        str_test = {
            str(post): post.text[:POST_STR_AMOUNT],
            str(group): group.title,
        }
        for model, string in str_test.items():
            with self.subTest(model=model):
                self.assertEqual(model, string)

    def test_verbose_name(self):
        """
        Проверяем verbose_name моделей.
        """
        post = PostModelTest.post
        field_verbose = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор поста',
            'group': 'Группа',
        }
        for field, value in field_verbose.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name,
                    value
                )

    def test_help_text(self):
        """
        Проверяем help_text моделей.
        """
        post = PostModelTest.post
        field_help_text = {
            'text': 'Введите текст поста',
            'pub_date': 'Это поле будет заполнено автоматически',
            'author': 'Автор поста',
            'group': (
                'Выберите группу, к которой будет относиться '
                'пост. Если группа не будет выбрана, тогда '
                'пост не будет относиться ни к одной группе.'
            ),
        }
        for field, value in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text,
                    value
                )
