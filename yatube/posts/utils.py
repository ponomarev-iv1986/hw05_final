from django.core.paginator import Paginator


def page_paginator(request, post_list, posts_amount):
    """Пагинатор на страницы."""
    paginator = Paginator(
        post_list,
        posts_amount
    )
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
