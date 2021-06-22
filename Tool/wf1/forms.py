from django import forms

from accounts.models import User
from wf1.widgets import PlainTextWidget
from wiki.models import Sentence
from wf1.validators import line_count_validator


class WF1ReviewForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(WF1ReviewForm, self).__init__(*args, **kwargs)
        self.fields['user'] = forms.ModelChoiceField(queryset=User.objects.all(), empty_label='Choose...',
                                                     widget=forms.Select(attrs={'class': 'form-control'}))


class Wf1aForm(forms.Form):

    def __init__(self, *args, page_id=None, **kwargs):
        super(Wf1aForm, self).__init__(*args, **kwargs)
        self.fields['page_id'] = forms.IntegerField(widget=forms.HiddenInput)
        self.fields['source_sentence'] = forms.ModelChoiceField(queryset=Sentence.objects.filter(page_id=page_id),
                                                                empty_label=None,
                                                                widget=forms.RadioSelect(attrs={"class": "sentence"})
                                                                )
        self.fields['claims'] = forms.CharField(validators=[line_count_validator], widget=forms.Textarea(attrs={"style": "direction:rtl"}))


class Wf1bForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(Wf1bForm, self).__init__(*args, **kwargs)
        self.fields['source_claim_id'] = forms.IntegerField(widget=forms.HiddenInput)
        self.fields['source_claim_content'] = forms.CharField(widget=PlainTextWidget)
        self.fields['rephrase'] = forms.CharField(validators=[line_count_validator],
                                                  widget=forms.Textarea(attrs={"style": "direction:rtl"}))
        self.fields['negate'] = forms.CharField(validators=[line_count_validator],
                                                widget=forms.Textarea(attrs={"style": "direction:rtl"}))
        self.fields['similar'] = forms.CharField(validators=[line_count_validator],
                                                 widget=forms.Textarea(attrs={"style": "direction:rtl"}))
        self.fields['dissimilar'] = forms.CharField(validators=[line_count_validator],
                                                    widget=forms.Textarea(attrs={"style": "direction:rtl"}))
        self.fields['specific'] = forms.CharField(validators=[line_count_validator],
                                                  widget=forms.Textarea(attrs={"style": "direction:rtl"}))
        self.fields['general'] = forms.CharField(validators=[line_count_validator],
                                                 widget=forms.Textarea(attrs={"style": "direction:rtl"}))
