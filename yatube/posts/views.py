from multiprocessing import context
from django.core.paginator import Paginator
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .models import Post
from .models import Group
from .models import User
from .models import Comment
from .forms import PostForm
from .forms import CommentForm
#from .forms import Follow
from .models import Follow



def paginator(request, post_list):
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj

#@cache_page(20 * 15)
def index(request):
    post_list = Post.objects.all()
    context = {
        'page_obj': paginator(request, post_list), }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.prefetch_related('group').filter(group=group)
    context = {
        'group': group,
        'page_obj': paginator(request, post_list),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    if Follow.objects.filter(author=author, user= request.user).exists():
        following= True
    else:
        following= False
    user= request.user
    post_list = author.posts.all()
    context = {
        'user': user,
        'following': following,
        "author": author,
        "page_obj": paginator(request, post_list),
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm()
    comment=Comment.objects.all().filter(post=post)
    context = {
        'post': post,
        'comment':comment,
        'form':form,}
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                files=request.FILES or None)
    if form.is_valid():
        create_post = form.save(commit=False)
        create_post.author = request.user
        create_post.save()
        return redirect('posts:profile', create_post.author)
    template = 'posts/create_post.html'
    context = {
        'form': form
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    template = 'posts/create_post.html'
    context = {
        'form': form,
        'is_edit': True,
        'post': post,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id) 
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    context = {
        'page_obj': paginator(request, post_list), }
    return render(request, 'posts/follow.html', context)

@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if Follow.objects.filter(author=author, user= request.user).exists() == False:
        Follow.objects.get_or_create(
            user=request.user,
            author=author,
        )
    else:
        None
    return redirect('posts:profile', username=username)

@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow= Follow.objects.get(author=author, user=request.user)
    follow.delete()
    return redirect('posts:profile', username=username)
