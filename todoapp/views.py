from django.shortcuts import render, redirect
from .forms import RegistrationForm
from .models import Task
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes

# Create your views here.


@login_required
def home(request):
    return render(request, 'index.html')

def register_view(request):

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = RegistrationForm()
    return render(request, 'register.html',{'form': form})

def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user :
            login(request, user)
            return redirect("dashboard")
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password'})
    return render(request, 'login.html')


def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        form = PasswordResetForm(data={'email': email})

        if form.is_valid():
            user = User.objects.filter(email=email).first()
            if user:
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                reset_link = request.build_absolute_uri(f'/reset/{uid}/{token}/')
                subject = 'Password reset request'
                message = render_to_string(
                    'registration/password_reset_email.html',
                    {
                        'user': user,
                        'email': user.email,
                        'protocol': 'http',
                        'domain': request.get_host(),
                        'uid': uid,
                        'token': token,
                    },
                )
                send_mail(subject, message, 'noreply@todogo.com', [user.email], fail_silently=False)
            return render(request, 'forgot_password.html', {'message': 'A password reset link has been sent to your email.'})

        return render(request, 'forgot_password.html', {'error': 'Please enter a valid registered email address.'})

    return render(request, 'forgot_password.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard_view(request):
    tasks = Task.objects.filter(user=request.user).order_by('-created_at')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            due_date = request.POST.get('due_date')
            priority = request.POST.get('priority', 'Low')

            if title and due_date:
                Task.objects.create(
                    user=request.user,
                    title=title,
                    description=description,
                    due_date=due_date,
                    priority=priority,
                )
            return redirect('dashboard')

        if action == 'complete':
            task_id = request.POST.get('task_id')
            if task_id:
                task = Task.objects.filter(user=request.user, id=task_id).first()
                if task:
                    task.completed = True
                    task.save()
            return redirect('dashboard')

        if action == 'delete':
            task_id = request.POST.get('task_id')
            if task_id:
                Task.objects.filter(user=request.user, id=task_id).delete()
            return redirect('dashboard')

    return render(request, 'dashboard.html', {'user': request.user, 'tasks': tasks})