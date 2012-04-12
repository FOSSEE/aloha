from django import forms
from allotter.models import Profile
from django.forms.extras.widgets import SelectDateWidget
from django.forms.widgets import RadioSelect

from django.utils.encoding import *

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Fieldset, HTML, ButtonHolder, Div

from string import digits, uppercase
import settings

BIRTH_YEAR_CHOICES = tuple(range(1960, 1994, 1))
DD_YEAR_CHOICES = (2012,)
CATEGORY_CHOICES = [('G','General'), ('B', 'OBC-NCL'), ('M', 'OBC-NCL (Minorities)'), 
                    ('C', 'SC'), ('T', 'ST')]
PD_CHOICES = [('Y', 'Yes'), ('N', 'No')]                                        


class UserLoginForm(forms.Form):
    
    ##Registration Number as Username
    username = forms.IntegerField(label="Registration Number", 
             help_text="As on your Examination Admit Card")
 
    ##Application number as password    
    #password = forms.CharField(label = "Application Number", 
    #         max_length=10, help_text="As on your Examination Admit Card")
    
    dob = forms.DateField(label="Date of Birth", 
            widget=SelectDateWidget(years=BIRTH_YEAR_CHOICES, attrs={"class":"span1"}),
            initial=datetime.date.today)
    
    dd_no = forms.CharField(label="Demand Draft Number",
            max_length=6, help_text="Valid DD Number")
    
    dd_date = forms.DateField(label="Date of Issue",
            help_text="Please ensure that Demand Draft is valid",
            widget=SelectDateWidget(years=DD_YEAR_CHOICES, attrs={"class":"span1"}),
            initial=datetime.date.today)
                            
    dd_amount = forms.IntegerField(label="Amount", 
                help_text="As mentioned on the brochure.")
    
    def clean_username(self):
        u_name = self.cleaned_data["username"]
        
        if not u_name:
            raise forms.ValidationError("Enter an username.")    
        
        ##Verifies whether username contains only digits and is not 
        ##longer than 7, i.e Username == Registration Number.
        if str(u_name).strip(digits) or len(str(u_name)) != 7:
            msg = "Invalid Registration Number"
            raise forms.ValidationError(msg)

        ##Verifying whether the user already exists in the database
        ##Raising error otherwise
        try:
            User.objects.get(username__exact = u_name)
            return u_name
        except User.DoesNotExist:
            raise forms.ValidationError("Entered Registration Number haven't appeared for JAM Exam.")

#    def clean_password(self):
#    
#        pwd = self.cleaned_data['password']
#        
        ##Verifying the length of application number and whether it contains
        ##only digits.

#        if str(pwd).strip(digits) and len(pwd) != 5:
#            msg = "Not a valid Application Number"
#            raise forms.ValidationError(msg)    
#        
#        return pwd
        
    def clean(self):
        super(UserLoginForm, self).clean()
        u_name = self.cleaned_data.get('username')
        pwd = settings.DEFAULT_PASSWORD
        dob = self.cleaned_data["dob"]
        dd_no = self.cleaned_data.get("dd_no")
        dd_date = self.cleaned_data.get("dd_date")
        dd_amount = self.cleaned_data.get("dd_amount")
        try:
            current_user = User.objects.get(username__exact = u_name)
            profile = current_user.get_profile()
            if profile.dob != dob:
                raise forms.ValidationError("Date of Birth doesn't match.")
        except User.DoesNotExist:
            raise forms.ValidationError("Correct the following errors and try logging in again.")

        ##Validating the DD Details
        
        if not dd_no and not dd_amount:
            raise forms.ValidationError("Fill in the Demand Draft Details") 
        elif len(dd_no) != 6 or dd_no.count('0') == 6 or dd_no.strip(digits):
            raise forms.ValidationError("Demand Draft Number you have entered is not valid.")       
        if dd_amount != 300:
            raise forms.ValidationError("Make sure the amount matches what is mentioned in brochure")
                  
      
        ##Authentication part
        user = authenticate(username = u_name, password = pwd)
        if not user:
            raise forms.ValidationError("Registration Number doesn't match.")
        user_profile = user.get_profile()
        user_profile.dd_no = dd_no
        user_profile.save()
        return user
        
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = 'id-loginform'
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.form_action = " "
        self.helper.add_input(Submit('submit', 'Submit'))
        super(UserLoginForm, self).__init__(*args, **kwargs)


class UserDetailsForm(forms.Form):

    def __init__(self, user, *args, **kwargs):
        self.user = user
        self.helper = FormHelper()
        self.helper.form_id = 'id-detailsform'
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.form_action = "/allotter/details/"
        self.helper.layout = Layout(
            Fieldset(
                'Enter the following details',
                'email',
                'phone_number',
                'category',
                HTML("""
                <div class="alert alert-info">
                The category you select is normally the one you have 
                specified at the time of applying for the JAM 2012 examination. 
                The category verification is only after submitting the relevant 
                documents and scrutiny by the JAM 2012 committee and the institute 
                for which you are applying.  Candidates applying under the new 
                category OBC-NCL (Minorities) should have specified OBC at the 
                time of applying for the JAM 2012 and would now have to submit the 
                additional relevant documents for this category.
                </div>"""),
                'pd',
                HTML("""
                <p>Aggregate Marks(in %) including all subjects.</p>
                """),
                'tenth_perc',
                'twelfth_perc',
                'bachelor_perc',
                HTML("""
                <p><br/> *Cannot be changed once submitted.</p>"""),
                HTML("""
                <p> **Pre-final year/semester if final result is awaited.</p>"""),
            ),
            ButtonHolder(
                Submit('submit', 'Submit Details', css_class='button white')
            )
        )
        super(UserDetailsForm, self).__init__(*args, **kwargs)

    email = forms.EmailField(label="Email Address", widget=forms.TextInput(attrs={"placeholder":"john@example.com",}),
                help_text="Enter a valid email id where you will able to receive correspondence from JAM 2012.")
    
    phone_number = forms.CharField(label="Phone number", max_length=15, 
                widget=forms.TextInput(attrs={"placeholder":"9876543210",}), 
                help_text="Phone number with code. For example 02225722545 (with neither spaces nor dashes)")
    
    category = forms.ChoiceField(widget=forms.Select(attrs={'class':'selector'}), 
                label="Category", choices=CATEGORY_CHOICES,
                help_text="")
                
    pd = forms.ChoiceField(label="Physical Disability", widget=RadioSelect, choices=PD_CHOICES)        
    
    tenth_perc = forms.CharField(label="Tenth Percentage", max_length=5, help_text="10th Standard")    
    
    twelfth_perc = forms.CharField(label="Twelfth Percentage", 
                    max_length=5, help_text="12th Standard (+2 of equivalent)")

    bachelor_perc = forms.CharField(label="Bachelors Degree*", max_length=5, help_text="Bachelors Degree")    
    
    def clean_phone_number(self):
        pno = self.cleaned_data['phone_number']
        if str(pno).strip(digits):
            raise forms.ValidationError("Not a valid phone number")
        return pno  
        
    def save(self):  
        cleaned_data = self.cleaned_data
        user_profile = self.user.get_profile()
        
        email = self.cleaned_data['email']
        phone_number = self.cleaned_data['phone_number']
        category = self.cleaned_data['category']
        pd_status = self.cleaned_data['pd']
        tenth = self.cleaned_data['tenth_perc']
        twelfth = self.cleaned_data['twelfth_perc']   
        bachelor = self.cleaned_data['bachelor_perc']
           
        if email and phone_number and tenth and twelfth and bachelor:
            user_profile.secondary_email = email
            user_profile.phone_number = phone_number
            user_profile.tenth_perc = tenth
            user_profile.twelfth_perc = twelfth
            user_profile.bachelors_perc = bachelor        
        else:
            raise forms.ValidationError("Make sure that you have entered all the details.")            
           
        
        user_application = user_profile.application
        user_application.cgy = category
        user_application.pd_status = pd_status
        user_application.save()    

        user_profile.save()
