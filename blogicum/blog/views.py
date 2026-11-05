"""Представления приложения blog."""

from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Page, Paginator
from django.db.models import Count, QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseBase
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, UpdateView

from .forms import CommentForm, PostForm, ProfileForm
from .models import Category, Comment, Post

User = get_user_model()

POSTS_PER_PAGE = 10


def get_posts(
    queryset: QuerySet | None = None,
    only_published: bool = True,
    with_comment_count: bool = True,
) -> QuerySet:
    """Возвращает посты со связанными объектами и, по желанию, фильтрами."""
    if queryset is None:
        queryset = Post.objects.all()
    queryset = queryset.select_related('category', 'location', 'author')
    if only_published:
        queryset = queryset.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now(),
        )
    if with_comment_count:
        queryset = queryset.annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')
    return queryset


def paginate(request: HttpRequest, queryset: QuerySet) -> Page:
    """Возвращает страницу пагинатора для переданного набора объектов."""
    paginator = Paginator(queryset, POSTS_PER_PAGE)
    return paginator.get_page(request.GET.get('page'))


def index(request: HttpRequest) -> HttpResponse:
    """Главная страница со списком публикаций."""
    return render(
        request,
        'blog/index.html',
        {'page_obj': paginate(request, get_posts())},
    )


def category_posts(request: HttpRequest, category_slug: str) -> HttpResponse:
    """Страница публикаций выбранной категории."""
    category = get_object_or_404(
        Category, slug=category_slug, is_published=True
    )
    return render(
        request,
        'blog/category.html',
        {
            'category': category,
            'page_obj': paginate(request, get_posts(category.posts.all())),
        },
    )


def profile(request: HttpRequest, username: str) -> HttpResponse:
    """Страница пользователя с его публикациями."""
    author = get_object_or_404(User, username=username)
    posts = get_posts(
        author.posts.all(),
        only_published=request.user != author,
    )
    return render(
        request,
        'blog/profile.html',
        {'profile': author, 'page_obj': paginate(request, posts)},
    )


@login_required
def edit_profile(request: HttpRequest) -> HttpResponse:
    """Редактирование профиля текущего пользователя."""
    form = ProfileForm(request.POST or None, instance=request.user)
    if form.is_valid():
        form.save()
        return redirect('blog:profile', request.user.username)
    return render(request, 'blog/user.html', {'form': form})


def post_detail(request: HttpRequest, post_id: int) -> HttpResponse:
    """Страница отдельной публикации с комментариями."""
    post = get_object_or_404(
        get_posts(only_published=False, with_comment_count=False),
        pk=post_id,
    )
    if post.author != request.user:
        post = get_object_or_404(
            get_posts(only_published=True, with_comment_count=False),
            pk=post_id,
        )
    return render(
        request,
        'blog/detail.html',
        {
            'post': post,
            'form': CommentForm(),
            'comments': post.comments.select_related('author'),
        },
    )


class PostCreateView(LoginRequiredMixin, CreateView):
    """Создание новой публикации."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form: PostForm) -> HttpResponse:
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse('blog:profile', args=(self.request.user.username,))


class PostAuthorMixin(LoginRequiredMixin):
    """Доступ к изменению публикации только для её автора."""

    model = Post
    template_name: str | None = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any,
    ) -> HttpResponseBase:
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        post = get_object_or_404(Post, pk=kwargs['post_id'])
        if post.author != request.user:
            return redirect('blog:post_detail', post.pk)
        return super().dispatch(request, *args, **kwargs)


class PostUpdateView(PostAuthorMixin, UpdateView):
    """Редактирование публикации."""

    form_class = PostForm

    def get_success_url(self) -> str:
        return reverse('blog:post_detail', args=(self.object.pk,))


class PostDeleteView(PostAuthorMixin, DeleteView):
    """Удаление публикации с подтверждением."""

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context

    def get_success_url(self) -> str:
        return reverse('blog:profile', args=(self.request.user.username,))


@login_required
def add_comment(request: HttpRequest, post_id: int) -> HttpResponse:
    """Добавление комментария к публикации."""
    post = get_object_or_404(get_posts(with_comment_count=False), pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', post_id)


class CommentAuthorMixin(LoginRequiredMixin):
    """Доступ к изменению комментария только для его автора."""

    model = Comment
    template_name: str | None = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'
    request: HttpRequest
    kwargs: dict[str, Any]

    def get_object(self, queryset: QuerySet | None = None) -> Comment:
        return get_object_or_404(
            Comment,
            pk=self.kwargs['comment_id'],
            post_id=self.kwargs['post_id'],
            author=self.request.user,
        )

    def get_success_url(self) -> str:
        return reverse('blog:post_detail', args=(self.kwargs['post_id'],))


class CommentUpdateView(CommentAuthorMixin, UpdateView):
    """Редактирование комментария."""

    form_class = CommentForm


class CommentDeleteView(CommentAuthorMixin, DeleteView):
    """Удаление комментария с подтверждением."""
