from django import forms


class AuthenticationForm(forms.Form):
    matrixServer = forms.CharField(widget=forms.URLInput, label='Server', max_length=100)
    username = forms.CharField(widget=forms.TextInput, label='Username', max_length=40)
    password = forms.CharField(widget=forms.PasswordInput, max_length=40)


class AddToChatForm(forms.Form):
    typedtext = forms.CharField(widget=forms.TextInput)
