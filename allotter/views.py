from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
from django.shortcuts import render, redirect
from django.template import RequestContext
from django.http import Http404

#TODO: Remove this if possible
from django.http import HttpResponseRedirect 
from django.core.urlresolvers import reverse

from django.contrib.auth.models import User
from allotter.models import Profile, Option, Exam
from allotter.forms import UserLoginForm, UserDetailsForm

from itertools import chain

#Reportlab libraries
from django.http import HttpResponse
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY

import time

def user_login(request):

    """Take the credentials of the user and log the user in."""

    user = request.user
    if user.is_authenticated():
        status = user.get_profile().application.submitted #Getting the submission status
        if status: #If already submitted, takes to Completion Page
            return HttpResponseRedirect(reverse('allotter.views.complete', args=(user.username,)))
        else: #Otherwise to Option Choosing Page   
            return redirect("/allotter/details")

    if request.method == "POST":
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data
            login(request, user)
            status = user.get_profile().application.submitted #Getting the submission status
            if status:
                return HttpResponseRedirect(reverse('allotter.views.complete', args=(user.username,)))
            else:    
                return redirect("/allotter/details")
        else:
            context = {"form": form}
            return render_to_response('allotter/login.html', context,
                        context_instance=RequestContext(request))
    else:
        form = UserLoginForm()
        context = {"form": form}
        return render_to_response('allotter/login.html', context,
                                     context_instance=RequestContext(request))
                                     

@login_required
def submit_details(request):
    """
        Get the secondary email address, phone number and save it to the Profile.
    """
    user = request.user
    
    if request.method == "POST":
        form = UserDetailsForm(user, request.POST)
        if form.is_valid():
            data = form.cleaned_data
            form.save()
            return redirect("/allotter/apply/")           
        else:
            return render_to_response('allotter/details.html',
                {'form':form},
                context_instance=RequestContext(request))  
                
    else:
        form = UserDetailsForm(request.user)
        context = {"form": form}
        return render_to_response('allotter/details.html', context,
                                     context_instance=RequestContext(request))              
       
def get_details(user, error_message = ""):
    """
       Retrieves the information about Test paper(s) and options available
       and returns them in a dictionary(context) for passing to the Template.
    """
    user_profile = user.get_profile()
    user_application = user_profile.application
    np = user_application.np #Number of Papers
    first_paper = user_application.first_paper #First Paper Name
    options_available_first = Option.objects.filter(exam__exam_name=first_paper).distinct() #Options for First paper
    oafl = len(options_available_first)  
    if np == 2: #If written two exams
        second_paper = user_application.second_paper
        options_available_second = Option.objects.filter(exam__exam_name=second_paper).distinct()
        oasl = len(options_available_second)
        context = {'user': user, 'first_paper': first_paper,
            'options_available_first' : options_available_first, 
            'second_paper': second_paper, 
            'options_available_second' : options_available_second,
            'np' : np, 'options_range': range(1, oafl + oasl + 1, 1), 
            'error_message': error_message}    
    else: #If written only one exam
        context = {'user': user, 'first_paper': first_paper,
            'options_available_first' : options_available_first,
            'options_range': range(1, oafl + 1, 1), 
            'np' : np, 'error_message' : error_message}     
    return context              
                                     
@login_required
def apply(request):
    """
        Displays the application page for an authenticated user.
    """
    user = request.user
    if not(user.is_authenticated()):
        return redirect('/allotter/login/')
    
    context = get_details(user) 
    ci = RequestContext(request)
              
    return render_to_response('allotter/apply.html', context,
        context_instance=ci)                         

##Logouts the user.

def user_logout(request):
    logout(request)
    return redirect ('/allotter/')

#TODO: Extensive Testing
                            
def submit_options(request, reg_no):
    """
        Gets the Options and their preference number through the POST object and
        stores them as list(sorted according to preferences). Options with None are 
        ignored. 
    """
    user = get_object_or_404(User, username=reg_no)
    user_profile = user.get_profile()
    user_application = user_profile.application
    np = user_application.np
    first_paper = user_application.first_paper #First Paper Name
    options_available_first = Option.objects.filter(exam__exam_name=first_paper).distinct() #Options for First paper
    
    if np == 2: #If qualified for second paper
        second_paper = user_application.second_paper #Second Paper Name
        options_available_second = Option.objects.filter(exam__exam_name=second_paper).distinct() #Options for second paper
        options_available_list = chain(options_available_first, options_available_second) #chaining the two lists
    else:
        options_available_list = options_available_first
        
    options_chosen_list = [] #Initializing empty list for storing options
    for option in options_available_list:   
        option_pref = request.POST[unicode(option.opt_code)]           
        options_chosen_list.append([option_pref, str(option.opt_code)]) #[preference, option code]
    
    options_chosen_list.sort() #Sorting by preference
    options_code_list = []
    for opt in options_chosen_list:
        if int(opt[0]): #ignoring the options for which None was marked
            options_code_list.append(opt[1])
         
    user_application.options_selected = options_code_list #Setting the attribute in model   
    user_application.submitted = True #Submission Status
    user_application.save()
    return HttpResponseRedirect(reverse('allotter.views.complete', args=(reg_no,)))

def complete(request, reg_no):
    user = get_object_or_404(User, username=reg_no)
    sec_email = user.get_profile().secondary_email
    options_chosen = get_chosen_options(user)
    context = {'user': reg_no, 'email': sec_email,  
                'options_chosen': options_chosen}
    ci = RequestContext(request)          
    return render_to_response('allotter/complete.html', context, context_instance=ci)
    
    
def get_chosen_options(user):
    user_profile = user.get_profile()
    user_application = user_profile.application
    np = user_application.np
    ocl = eval(user_application.options_selected)
    chosen_options = []
    for oc in ocl:
        chosen_options.append(Option.objects.get(opt_code=int(oc))) 
    return chosen_options
        
def generate_pdf(request, reg_no="1234567"):
    user = get_object_or_404(User, username=reg_no)
    user_profile = user.get_profile()
    user_application = user_profile.application
    np = user_application.np
 
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=JAM2012_Allottment.pdf'
    
    elements = []
    doc = SimpleDocTemplate(response)
    
    formatted_time = time.ctime()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
    
    ptext = '<font size=15>JAM 2012 Allotment.</font>'         
    elements.append(Paragraph(ptext, styles["Justify"]))
    elements.append(Spacer(4, 20))
    
    ptext = '<font size=12>Registration Number: %s</font>' % reg_no 
    elements.append(Paragraph(ptext, styles["Normal"]))
    elements.append(Spacer(1, 12))
    
    ptext = '<font size=12>Number of Papers Eligible: %s</font>' % np
    elements.append(Paragraph(ptext, styles["Normal"]))
    elements.append(Spacer(1, 12))
    
    ptext = '<font size=12>Following are the options in order of preference</font>' 
    elements.append(Paragraph(ptext, styles["Normal"]))
    elements.append(Spacer(1, 12))
    
    data = []   
    options = get_chosen_options(user)
    counter = 1
    for opt in options:
        data.append([counter, opt.opt_code, opt.opt_location, opt.opt_name])
        counter = counter + 1
            
    t = Table(data)
    t.setStyle(TableStyle([('GRID',(0,0),(3,len(options)),1,colors.black),
                                   ('TEXTCOLOR',(0,0),(0,-1),colors.green)]))
                                                                     
    elements.append(t)  
    
    ptext = '<font size=12>%s</font>' % formatted_time
    elements.append(Paragraph(ptext, styles["Normal"]))
    elements.append(Spacer(1, 12))
    
      
    doc.build(elements)
       
    return response    
    


