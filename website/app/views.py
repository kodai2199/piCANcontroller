from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
import json
from django.core import serializers
from .models import Installation, Command


def parse_alarms(installations):
    # Parse the alarms dictionary for every installation,
    # and just give an output string. This will make the
    # dashboard.html template much easier to understand
    alarms_strings = {}
    for i in installations:
        alarms = json.loads(i.alarms)
        counter = 0
        alarms_strings[i.id] = ""
        for alarm_id in alarms:
            counter += 1
            if counter != 1:
                alarms_strings[i.id] += " ,"
            alarms_strings[i.id] += f"#{alarm_id}"
        if counter == 0:
            alarms_strings[i.id] += "NESSUNO"
    return alarms_strings

@login_required
def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    # Loads the list of installations
    installations = Installation.objects.all()
    alarms_strings = parse_alarms(installations)

    # TODO pending commands block further actions on the same installations
    context = {
        'installations': installations,
        'alarms_strings': alarms_strings,
        'installations_count': installations.count(),
    }

    return render(request, 'dashboard.html', context=context)


@login_required
def toggle_installation(request):
    # Authentication is required to send a command
    if request.user.is_authenticated and request.method == "POST":
        imei = request.POST.get("imei", '')
        command = request.POST.get("command", '')
        command_queue = Command.objects.filter(imei=imei)
        if command_queue.count() >= 1:
            return HttpResponse('There already is a command being executed for this installation.')
        if command == "run":
            c = Command(imei=imei, command_string="RUN")
            c.save()
            print("RUN command sent to installation with imei {}".format(imei))
            return HttpResponse('success')
        elif command == "stop":
            c = Command(imei=imei, command_string="STOP")
            c.save()
            print("STOP command sent to installation with imei {}".format(imei))
            return HttpResponse('success')
        else:
            return HttpResponse('Invalid command')
    else:
        return HttpResponse('You need to login and use a correct syntax to send commands.')


@login_required
def reset_time_limit(request):
    # Authentication is required to send a command
    if request.user.is_authenticated and request.method == "POST":
        # check that the user is an administrator
        if request.user.groups.filter(name="admin").exists():
            imei = request.POST.get("imei", '')
            code = request.POST.get("code", '')
            field_type = request.POST.get("field_type", '')
            command_queue = Command.objects.filter(imei=imei)
            if command_queue.count() >= 1:
                return HttpResponse('There already is a command being executed for this installation.')
            if field_type == "tl" and code == "reset_time_limit":
                c = Command(imei=imei, command_string="RESET_TL")
                c.save()
                return HttpResponse('success')
            elif field_type == "bk" and code == "reset_backup":
                c = Command(imei=imei, command_string="RESET_BK")
                c.save()
                return HttpResponse('success')
            elif field_type == "rb" and code == "reset_whatever":
                c = Command(imei=imei, command_string="RESET_RB")
                c.save()
                return HttpResponse('success')
            else:
                return HttpResponse('Invalid command')
        else:
            return HttpResponse('Insufficient permissions')


@login_required
def update_data(request):
    # Authentication is required to send a command
    if request.user.is_authenticated and request.method == "POST":
        installations = Installation.objects.all()
        alarms_strings = parse_alarms(installations)
        installations_json = serializers.serialize("json", installations)
        return HttpResponse(installations_json, content_type='application/json')