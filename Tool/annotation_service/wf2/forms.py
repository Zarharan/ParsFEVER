from django import forms

from accounts.models import User
from wiki.models import Sentence


class CheckSentencesForm(forms.Form):

    def __init__(self, *args, sentences=None, **kwargs):
        super(CheckSentencesForm, self).__init__(*args, **kwargs)
        self.fields['page_id'] = forms.IntegerField(widget=forms.HiddenInput)
        self.fields['crawled_html'] = forms.CharField(widget=forms.HiddenInput)
        self.fields['source_sentence'] = forms.ChoiceField(choices=sentences,
                                                           widget=forms.RadioSelect(attrs={"class": "sentence"})
                                                           )


class Wf2Form(forms.Form):

    def __init__(self, *args, **kwargs):
        super(Wf2Form, self).__init__(*args, **kwargs)
        self.fields['claim_id'] = forms.IntegerField(widget=forms.HiddenInput)


class WF2ReviewForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(WF2ReviewForm, self).__init__(*args, **kwargs)
        self.fields['user'] = forms.ModelChoiceField(queryset=User.objects.all(), empty_label='Choose...',
                                                     widget=forms.Select(attrs={'class': 'form-control'}))
