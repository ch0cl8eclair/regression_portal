from django import forms
import re



class MessageForm(forms.Form):
    message = forms.CharField(max_length=6, required=False)

    MSG_PATTERN = re.compile("\w{6}(_\d+)*")
    
    def clean_message(self):
        message = self.cleaned_data.get('message', '')
        print "matching: '%s'" % message
        match = MessageForm.MSG_PATTERN.match(message)
        if not match:
            raise forms.ValidationError("Invalid message format")
        return message
        