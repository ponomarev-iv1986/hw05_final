from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

# Константа, указывающая сколько символов будет
# выводиться при методе __str__ в модели Post
POST_STR_AMOUNT: int = 15

# Константа, указывающая сколько символов будет
# выводиться при методе __str__ в модели Comment
COMMENT_STR_AMOUNT: int = 15


class Post(models.Model):
    """Модель Post."""

    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Введите текст поста'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        help_text='Это поле будет заполнено автоматически',
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор поста',
        help_text='Автор поста',
        on_delete=models.CASCADE,
        related_name='posts'
    )
    group = models.ForeignKey(
        'Group',
        verbose_name='Группа',
        help_text=(
            'Выберите группу, к которой будет относиться '
            'пост. Если группа не будет выбрана, тогда '
            'пост не будет относиться ни к одной группе.'
        ),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts'
    )
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:POST_STR_AMOUNT]


class Group(models.Model):
    """Модель Group."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Comment(models.Model):
    """Модель для комментирования постов."""

    post = models.ForeignKey(
        Post,
        verbose_name='Комментируемый пост',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор комментария',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField(
        'Текст комментария',
        help_text='Введите комментарий'
    )
    created = models.DateTimeField(
        'Дата',
        help_text='Это поле будет заполнено автоматически',
        auto_now_add=True
    )

    def __str__(self):
        return self.text[:COMMENT_STR_AMOUNT]


class Follow(models.Model):
    """Модель для подпсиок на авторов."""

    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Подписка',
        on_delete=models.CASCADE,
        related_name='following'
    )
