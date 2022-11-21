from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post
from .utils import page_paginator

User = get_user_model()

# Константа, указывающая по сколько постов выводить
POSTS_AMOUNT: int = 10


@cache_page(20, key_prefix='index_page')
@vary_on_cookie
def index(request):
    """Главная страница."""
    template = 'posts/index.html'
    post_list = Post.objects.prefetch_related(
        'author'
    ).prefetch_related(
        'group'
    ).all()
    page_obj = page_paginator(
        request,
        post_list,
        POSTS_AMOUNT
    )
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    """Страница с постами по группам."""
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.prefetch_related(
        'author'
    ).all()
    page_obj = page_paginator(
        request,
        post_list,
        POSTS_AMOUNT
    )
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    """Профайл пользователя."""
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    if request.user.is_authenticated:
        following = request.user.follower.filter(
            author=author
        ).exists()
    else:
        following = False
    post_list = author.posts.prefetch_related(
        'group'
    ).all()
    count = post_list.count()
    page_obj = page_paginator(
        request,
        post_list,
        POSTS_AMOUNT
    )
    context = {
        'count': count,
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    """Страница просмотра записи."""
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post=post)
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    """Страница для публикации постов."""
    template = 'posts/create_post.html'

    if request.method == 'POST':
        form = PostForm(
            request.POST,
            files=request.FILES or None
        )
        if form.is_valid():
            form.instance.author = request.user
            form.save()
            return redirect('posts:profile', request.user)
        return render(request, template, {'form': form})
    form = PostForm()
    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    """Страница редактирования постов."""
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)

    if post.author != request.user:
        return redirect('posts:post_detail', post_id)

    if request.method == 'POST':
        form = PostForm(
            request.POST,
            files=request.FILES or None,
            instance=post
        )
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id)
        return render(
            request,
            template,
            {
                'form': form,
                'is_edit': True,
                'post': post,
            }
        )
    form = PostForm(instance=post)
    return render(
        request,
        template,
        {
            'form': form,
            'is_edit': True,
            'post': post,
        }
    )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id)


@login_required
def follow_index(request):
    """Страница с подписками пользователя."""
    template = 'posts/follow.html'
    post_list = Post.objects.filter(
        author__following__user=request.user
    )
    page_obj = page_paginator(
        request,
        post_list,
        POSTS_AMOUNT
    )
    context = {'page_obj': page_obj}
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    """Подписаться."""
    author = get_object_or_404(User, username=username)
    if author != request.user:
        if not request.user.follower.filter(
            author=author
        ).exists():
            Follow.objects.create(
                user=request.user,
                author=author
            )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    """Отписаться."""
    author = get_object_or_404(User, username=username)
    data = request.user.follower.filter(author=author)
    if data.exists():
        data.delete()
    return redirect('posts:profile', username)
