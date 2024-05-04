from multiprocessing import context
from urllib.request import Request
from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required

from base.models import Room, Topic, Message
from .forms import RoomForm,UserForm

def loginUser(request):
    page = 'login'
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            user = User.objects.get(username == username)
        except:
            messages.error(request,'User does not exist')
        user = authenticate(request , username = username, password = password)
        
        if user is not None:
            login(request , user)
            return redirect('home')
        else :
            messages.error(request, 'Username or password is not correct')
        
    context = {'page':page}
    return render(request, 'base/login_register.html',context)

def logoutUser(request):
    logout(request)
    return redirect('home')

def registerUser(request):
    page = 'register'
    form = UserCreationForm()
    if form.is_valid():
        user = form.save(commit= False)
        user.username = user.username.lower() 
        user.save()
        login(request, user)
        return redirect('home')
    else:
        messages.error(request, 'An error occured during registration')
    context = {'page':page,'form':form}
    return render(request, 'base/login_register.html',context)

def userProfile(request, pk : int):
    user = User.objects.get(id = pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    print(room_messages)
    topics = Topic.objects.all()
    context = {'user':user,
               'rooms':rooms,
               'room_messages':room_messages,
               'topics':topics}
    return render(request, 'base/profile.html',context)


def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    rooms = Room.objects.filter(
        Q(topic__name__icontains = q) |
        Q(name__icontains = q) |
        Q(description__icontains = q) 
    )
    topics = Topic.objects.all()
    room_count = rooms.count()
    
    room_messages = Message.objects.filter(Q(room__topic__name__icontains = q))
    context = {'rooms': rooms, 'topics': topics,'room_count':room_count,'room_messages':room_messages}
    return render(request, 'base/home.html',context=context)

def room(request,pk):
    room =Room.objects.get(id = int(pk))
    room_messages = room.message_set.all().order_by('-created')
    participants = room.participants.all()
    if request.method == 'POST':
        message = Message.objects.create(
            user = request.user,
            room =  room,
            body = request.POST.get('body')
        )
        room.participants.add(request.user)        
        return redirect('room',pk= room.id)
    context = {
        'room':room, 
        'room_messages':room_messages,
        'participants' : participants
        }
    return render(request, 'base/room.html', context=context)

@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == "POST": 
        topic_name = request.POST.get('topic')
        topic,created = Topic.objects.get_or_create(name = topic_name)
        Room.objects.create(
            host = request.user,
            topic = topic, 
            name = request.POST.get('name'),
            description = request.POST.get('description')
        )
        # form = RoomForm(request.POST)
        # if form.is_valid():
        #     room = form.save(commit = False)
        #     room.host= request.user 
        #     room.topic = topic
        #     room.save()
        return redirect('home')
    context = {
        'form':form,
        'topics':topics
        }
    return render(request, 'base/room_form.html',context)

@login_required(login_url='login')
def editRoom(request,pk):
    room = Room.objects.get(id = int(pk))
    topics = Topic.objects.all()
    if request.user != room.host:
        return HttpResponse("You have no permission.")
    if request.method == "POST":
        topic_name = request.POST.get('topic')
        topic,created = Topic.objects.get_or_create(name = topic_name)
        # form = RoomForm(request.POST, instance = room)
        # if form.is_valid():
        #     form.save()
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('home')
        
    form = RoomForm(instance=room)
    context = {"form":form,
               "topics":topics,
               "room":room
               }
    return render(request, 'base/room_form.html',context)

@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id = int(pk))
    
    if request.user != room.host:
        return HttpResponse("You have no permission.")
    if request.method == "POST":
        room.delete()
        return redirect('home')
    return render(request, 'base/delete.html' , {'obj':room})

@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id = int(pk))
    room = message.room
    if request.user != message.user:
        return HttpResponse("You have no permission.")
    if request.method == "POST":
        message.delete()
        return redirect('room',pk = room.id)
    return render(request, 'base/delete.html' , {'obj':message})

@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk = user.id)
    context = {'form':form}
    return render(request, 'base/update-user.html',context)